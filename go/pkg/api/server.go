// REST API server for COINjecture
package api

import (
	"context"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/config"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/ipfs"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/limiter"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/p2p"
	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// Prometheus metrics
var (
	httpRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "coinjecture_http_requests_total",
			Help: "Total HTTP requests by endpoint and status",
		},
		[]string{"endpoint", "method", "status"},
	)

	httpRequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "coinjecture_http_request_duration_seconds",
			Help:    "HTTP request duration in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"endpoint", "method"},
	)

	proofSubmissionsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "coinjecture_proof_submissions_total",
			Help: "Total proof submissions by result",
		},
		[]string{"result"}, // result: accepted, rejected_syntax, rejected_verify, rejected_backpressure
	)

	proofVerifyDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "coinjecture_proof_verify_duration_ms",
			Help:    "Proof verification duration in milliseconds",
			Buckets: []float64{10, 50, 100, 500, 1000, 5000, 10000},
		},
		[]string{"tier"},
	)

	backpressureRejectionsTotal = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "coinjecture_backpressure_rejections_total",
			Help: "Total requests rejected due to backpressure (queue full)",
		},
	)
)

// Server is the REST API server
type Server struct {
	config      config.APIConfig
	log         *logger.Logger
	limiter     *limiter.RateLimiter
	ipfsClient  *ipfs.IPFSClient
	p2pManager  *p2p.Manager
	router      *gin.Engine
	httpServer  *http.Server
}

// NewServer creates a new API server
func NewServer(
	cfg config.APIConfig,
	rateLimiter *limiter.RateLimiter,
	ipfsClient *ipfs.IPFSClient,
	p2pManager *p2p.Manager,
	log *logger.Logger,
) *Server {
	// Set Gin mode
	gin.SetMode(gin.ReleaseMode)

	router := gin.New()
	router.Use(gin.Recovery())

	s := &Server{
		config:     cfg,
		log:        log,
		limiter:    rateLimiter,
		ipfsClient: ipfsClient,
		p2pManager: p2pManager,
		router:     router,
	}

	s.setupRoutes()
	return s
}

// setupRoutes configures API routes
func (s *Server) setupRoutes() {
	// Middleware
	s.router.Use(s.rateLimitMiddleware())
	s.router.Use(s.loggingMiddleware())

	if s.config.EnableCORS {
		s.router.Use(corsMiddleware())
	}

	// Health check
	s.router.GET("/health", s.handleHealth)

	// Prometheus metrics endpoint
	s.router.GET("/metrics", gin.WrapH(promhttp.Handler()))

	// API v1
	v1 := s.router.Group("/v1")
	{
		v1.POST("/submit_proof", s.handleSubmitProof)
		v1.GET("/block/:hash", s.handleGetBlock)
		v1.GET("/block/latest", s.handleGetLatestBlock)
		v1.GET("/ipfs/:cid", s.handleGetIPFS)
		v1.GET("/status", s.handleStatus)
	}
}

// Start starts the API server
func (s *Server) Start() error {
	addr := fmt.Sprintf("%s:%d", s.config.Host, s.config.Port)

	s.httpServer = &http.Server{
		Addr:         addr,
		Handler:      s.router,
		ReadTimeout:  s.config.ReadTimeout,
		WriteTimeout: s.config.WriteTimeout,
	}

	s.log.WithField("address", addr).Info("API server starting")
	return s.httpServer.ListenAndServe()
}

// Shutdown gracefully shuts down the server
func (s *Server) Shutdown(ctx context.Context) error {
	if s.httpServer != nil {
		return s.httpServer.Shutdown(ctx)
	}
	return nil
}

// Middleware

func (s *Server) rateLimitMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		allowed, err := s.limiter.CheckRequest(c.Request.RemoteAddr)
		if !allowed {
			s.log.WithError(err).WithField("ip", c.ClientIP()).Warn("Rate limit exceeded")
			c.JSON(http.StatusTooManyRequests, gin.H{
				"error": "rate limit exceeded",
			})
			c.Abort()
			return
		}
		c.Next()
	}
}

func (s *Server) loggingMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		method := c.Request.Method

		c.Next()

		duration := time.Since(start)
		status := c.Writer.Status()

		// Prometheus metrics
		httpRequestsTotal.WithLabelValues(path, method, strconv.Itoa(status)).Inc()
		httpRequestDuration.WithLabelValues(path, method).Observe(duration.Seconds())

		// Logging
		s.log.WithFields(logger.Fields{
			"method":   method,
			"path":     path,
			"status":   status,
			"duration": duration,
			"ip":       c.ClientIP(),
		}).Info("API request")
	}
}

func corsMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}

		c.Next()
	}
}

// Handlers

func (s *Server) handleHealth(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "healthy",
		"version": "4.0.0",
	})
}

func (s *Server) handleSubmitProof(c *gin.Context) {
	// Check backpressure FIRST (early reject before parsing/validation)
	nearCapacity, utilization := s.limiter.CheckBackpressure()
	if nearCapacity {
		backpressureRejectionsTotal.Inc()
		proofSubmissionsTotal.WithLabelValues("rejected_backpressure").Inc()

		s.log.WithField("queue_utilization", utilization).Warn("Backpressure: rejecting proof submission")

		retryAfter := int(10 * utilization) // Scale retry time with utilization
		c.Header("Retry-After", strconv.Itoa(retryAfter))

		c.JSON(http.StatusTooManyRequests, gin.H{
			"error":            "verification queue at capacity",
			"queue_utilization": fmt.Sprintf("%.1f%%", utilization*100),
			"retry_after_seconds": retryAfter,
		})
		return
	}

	// Parse request body
	var proof struct {
		ProblemType string   `json:"problem_type" binding:"required"`
		Tier        string   `json:"tier" binding:"required"`
		Elements    []int    `json:"elements" binding:"required"`
		Target      int      `json:"target" binding:"required"`
		Solution    []int    `json:"solution" binding:"required"`
		Commitment  string   `json:"commitment" binding:"required"`
		Timestamp   int64    `json:"timestamp" binding:"required"`
	}

	if err := c.ShouldBindJSON(&proof); err != nil {
		proofSubmissionsTotal.WithLabelValues("rejected_syntax").Inc()
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "invalid proof format",
			"details": err.Error(),
		})
		return
	}

	// Early reject: Check tier bounds (before expensive verification)
	if proof.Tier != "MOBILE" && proof.Tier != "DESKTOP" && proof.Tier != "SERVER" {
		proofSubmissionsTotal.WithLabelValues("rejected_syntax").Inc()
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "invalid tier",
			"valid_tiers": []string{"MOBILE", "DESKTOP", "SERVER"},
		})
		return
	}

	// Early reject: Check problem size bounds
	if len(proof.Elements) > 1000 || len(proof.Solution) > 100 {
		proofSubmissionsTotal.WithLabelValues("rejected_syntax").Inc()
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "proof size exceeds limits",
			"max_elements": 1000,
			"max_solution_size": 100,
		})
		return
	}

	// Early reject: Check timestamp (not too far in future/past)
	now := time.Now().Unix()
	if proof.Timestamp > now+300 || proof.Timestamp < now-3600 {
		proofSubmissionsTotal.WithLabelValues("rejected_syntax").Inc()
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "timestamp out of acceptable range",
			"now": now,
			"proof_timestamp": proof.Timestamp,
		})
		return
	}

	// Verify proof with Rust consensus engine (if CGO available)
	isValid, verifyErr := verifyProofWithRust(&proof, proof.Tier)
	if verifyErr != nil {
		proofSubmissionsTotal.WithLabelValues("rejected_verify").Inc()
		s.log.WithError(verifyErr).WithField("tier", proof.Tier).Error("Proof verification failed")
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "proof verification failed",
			"details": verifyErr.Error(),
		})
		return
	}

	if !isValid {
		proofSubmissionsTotal.WithLabelValues("rejected_verify").Inc()
		s.log.WithField("tier", proof.Tier).Warn("Proof solution invalid")
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "invalid proof solution",
		})
		return
	}

	// Proof is valid
	proofSubmissionsTotal.WithLabelValues("accepted").Inc()

	s.log.WithFields(logger.Fields{
		"tier": proof.Tier,
		"problem_size": len(proof.Elements),
		"solution_size": len(proof.Solution),
	}).Info("Proof submission accepted")

	c.JSON(http.StatusAccepted, gin.H{
		"status": "accepted",
		"message": "proof queued for verification",
		"tier": proof.Tier,
	})
}

func (s *Server) handleGetBlock(c *gin.Context) {
	hash := c.Param("hash")

	// TODO: Retrieve block from storage

	c.JSON(http.StatusNotImplemented, gin.H{
		"error": "not implemented yet",
		"hash":  hash,
	})
}

func (s *Server) handleGetLatestBlock(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{
		"error": "not implemented yet",
	})
}

func (s *Server) handleGetIPFS(c *gin.Context) {
	cid := c.Param("cid")

	// Get content from IPFS
	reader, err := s.ipfsClient.Get(c.Request.Context(), cid)
	if err != nil {
		s.log.WithError(err).WithField("cid", cid).Error("Failed to get IPFS content")
		c.JSON(http.StatusNotFound, gin.H{
			"error": "CID not found",
		})
		return
	}
	defer reader.Close()

	// Stream content
	c.DataFromReader(http.StatusOK, -1, "application/octet-stream", reader, nil)
}

func (s *Server) handleStatus(c *gin.Context) {
	status := map[string]interface{}{
		"api_version":  "4.0.0",
		"rate_limiter": s.limiter.Stats(),
		"ipfs_quorum":  s.ipfsClient.QuorumStatus(),
		"p2p_peers":    s.p2pManager.PeerCount(),
	}

	c.JSON(http.StatusOK, status)
}
