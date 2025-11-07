// COINjecture Validator Key Generation Utility
// Institutional-grade Ed25519 keypair generation with security hardening
// Version: 4.5.0+

package main

import (
	"crypto/rand"
	"encoding/hex"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"time"

	"golang.org/x/crypto/ed25519"
	"gopkg.in/yaml.v3"
)

const (
	// Version information
	Version = "4.5.0+"

	// File permissions (institutional security standards)
	PrivateKeyFileMode = 0600 // Owner read/write only
	PublicKeyFileMode  = 0644 // Owner read/write, others read
	ConfigFileMode     = 0640 // Owner read/write, group read

	// Key sizes
	PublicKeySize  = ed25519.PublicKeySize  // 32 bytes
	PrivateKeySize = ed25519.PrivateKeySize // 64 bytes
)

// KeyPair represents an Ed25519 keypair with metadata
type KeyPair struct {
	PublicKey  ed25519.PublicKey  `yaml:"public_key"`
	PrivateKey ed25519.PrivateKey `yaml:"-"` // Never serialize private key
	Created    time.Time          `yaml:"created"`
	Version    string             `yaml:"version"`
}

// KeyMetadata stores public key information for sharing
type KeyMetadata struct {
	PublicKeyHex string    `yaml:"public_key_hex"`
	Created      time.Time `yaml:"created"`
	Version      string    `yaml:"version"`
	Comment      string    `yaml:"comment,omitempty"`
}

// Config represents command-line configuration
type Config struct {
	OutputDir    string
	Count        int
	Prefix       string
	NoFiles      bool
	JsonOutput   bool
	Verbose      bool
	SecureRandom bool
}

func main() {
	config := parseFlags()

	if config.Verbose {
		fmt.Printf("COINjecture Validator Keygen v%s\n", Version)
		fmt.Printf("Generating %d Ed25519 keypair(s)...\n\n", config.Count)
	}

	// Ensure output directory exists
	if !config.NoFiles {
		if err := os.MkdirAll(config.OutputDir, 0750); err != nil {
			fatal("Failed to create output directory: %v", err)
		}
	}

	// Generate keypairs
	keypairs := make([]*KeyPair, config.Count)
	for i := 0; i < config.Count; i++ {
		kp, err := generateKeypair(config.SecureRandom)
		if err != nil {
			fatal("Failed to generate keypair %d: %v", i+1, err)
		}
		keypairs[i] = kp

		if config.Verbose {
			fmt.Printf("Generated keypair %d/%d\n", i+1, config.Count)
		}
	}

	// Save keypairs to files
	if !config.NoFiles {
		for i, kp := range keypairs {
			filename := fmt.Sprintf("%s%d", config.Prefix, i+1)
			if err := saveKeypair(kp, config.OutputDir, filename); err != nil {
				fatal("Failed to save keypair %d: %v", i+1, err)
			}

			if config.Verbose {
				fmt.Printf("Saved keypair to %s\n", filepath.Join(config.OutputDir, filename))
			}
		}
	}

	// Output keypairs to stdout
	if config.JsonOutput {
		printJSON(keypairs)
	} else {
		printHumanReadable(keypairs, config.Verbose)
	}

	if config.Verbose {
		fmt.Println("\n✓ Key generation complete")
		fmt.Println("\nSECURITY REMINDER:")
		fmt.Println("  - Private keys stored with 0600 permissions (owner read/write only)")
		fmt.Println("  - Never commit private keys to version control")
		fmt.Println("  - Use Hardware Security Modules (HSMs) in production")
		fmt.Println("  - Enable key rotation for institutional security")
	}
}

// parseFlags parses command-line flags with institutional defaults
func parseFlags() *Config {
	config := &Config{}

	flag.StringVar(&config.OutputDir, "output", "./keys", "Output directory for key files")
	flag.IntVar(&config.Count, "count", 1, "Number of keypairs to generate")
	flag.StringVar(&config.Prefix, "prefix", "validator", "Filename prefix for generated keys")
	flag.BoolVar(&config.NoFiles, "no-files", false, "Don't write files, only print to stdout")
	flag.BoolVar(&config.JsonOutput, "json", false, "Output in JSON format")
	flag.BoolVar(&config.Verbose, "verbose", true, "Verbose output")
	flag.BoolVar(&config.SecureRandom, "secure", true, "Use crypto/rand for secure random generation")

	showVersion := flag.Bool("version", false, "Show version and exit")
	flag.Parse()

	if *showVersion {
		fmt.Printf("coinjecture-keygen version %s\n", Version)
		os.Exit(0)
	}

	// Validate config
	if config.Count < 1 {
		fatal("Count must be at least 1")
	}
	if config.Count > 100 {
		fatal("Count cannot exceed 100 (safety limit)")
	}

	return config
}

// generateKeypair generates a new Ed25519 keypair with institutional security
func generateKeypair(secure bool) (*KeyPair, error) {
	var publicKey ed25519.PublicKey
	var privateKey ed25519.PrivateKey
	var err error

	if secure {
		// Use crypto/rand for cryptographically secure random generation
		publicKey, privateKey, err = ed25519.GenerateKey(rand.Reader)
	} else {
		// Fallback to less secure random (NOT recommended for production)
		publicKey, privateKey, err = ed25519.GenerateKey(nil)
	}

	if err != nil {
		return nil, fmt.Errorf("key generation failed: %w", err)
	}

	// Verify key sizes (safety check)
	if len(publicKey) != PublicKeySize {
		return nil, fmt.Errorf("invalid public key size: got %d, expected %d", len(publicKey), PublicKeySize)
	}
	if len(privateKey) != PrivateKeySize {
		return nil, fmt.Errorf("invalid private key size: got %d, expected %d", len(privateKey), PrivateKeySize)
	}

	return &KeyPair{
		PublicKey:  publicKey,
		PrivateKey: privateKey,
		Created:    time.Now().UTC(),
		Version:    Version,
	}, nil
}

// saveKeypair saves keypair to files with institutional security standards
func saveKeypair(kp *KeyPair, dir, filename string) error {
	// Save private key (0600 permissions - owner only)
	privateKeyPath := filepath.Join(dir, filename+".priv")
	privateKeyHex := hex.EncodeToString(kp.PrivateKey)
	if err := os.WriteFile(privateKeyPath, []byte(privateKeyHex), PrivateKeyFileMode); err != nil {
		return fmt.Errorf("failed to write private key: %w", err)
	}

	// Save public key (0644 permissions - world readable)
	publicKeyPath := filepath.Join(dir, filename+".pub")
	publicKeyHex := hex.EncodeToString(kp.PublicKey)
	if err := os.WriteFile(publicKeyPath, []byte(publicKeyHex), PublicKeyFileMode); err != nil {
		return fmt.Errorf("failed to write public key: %w", err)
	}

	// Save metadata YAML (0640 permissions - owner + group)
	metadata := KeyMetadata{
		PublicKeyHex: publicKeyHex,
		Created:      kp.Created,
		Version:      kp.Version,
		Comment:      fmt.Sprintf("COINjecture validator keypair - generated %s", kp.Created.Format(time.RFC3339)),
	}

	metadataPath := filepath.Join(dir, filename+".yaml")
	data, err := yaml.Marshal(metadata)
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}

	if err := os.WriteFile(metadataPath, data, ConfigFileMode); err != nil {
		return fmt.Errorf("failed to write metadata: %w", err)
	}

	return nil
}

// printHumanReadable prints keypairs in human-readable format
func printHumanReadable(keypairs []*KeyPair, verbose bool) {
	if !verbose {
		fmt.Println("\n=== Generated Keypairs ===\n")
	}

	for i, kp := range keypairs {
		fmt.Printf("Keypair #%d:\n", i+1)
		fmt.Printf("  Public Key:  %s\n", hex.EncodeToString(kp.PublicKey))
		fmt.Printf("  Private Key: %s\n", hex.EncodeToString(kp.PrivateKey))
		if verbose {
			fmt.Printf("  Created:     %s\n", kp.Created.Format(time.RFC3339))
			fmt.Printf("  Version:     %s\n", kp.Version)
		}
		fmt.Println()
	}
}

// printJSON prints keypairs in JSON format (for scripting)
func printJSON(keypairs []*KeyPair) {
	fmt.Println("[")
	for i, kp := range keypairs {
		fmt.Printf("  {\n")
		fmt.Printf("    \"public_key\": \"%s\",\n", hex.EncodeToString(kp.PublicKey))
		fmt.Printf("    \"private_key\": \"%s\",\n", hex.EncodeToString(kp.PrivateKey))
		fmt.Printf("    \"created\": \"%s\",\n", kp.Created.Format(time.RFC3339))
		fmt.Printf("    \"version\": \"%s\"\n", kp.Version)
		if i < len(keypairs)-1 {
			fmt.Printf("  },\n")
		} else {
			fmt.Printf("  }\n")
		}
	}
	fmt.Println("]")
}

// fatal prints error and exits with non-zero status
func fatal(format string, args ...interface{}) {
	fmt.Fprintf(os.Stderr, "ERROR: "+format+"\n", args...)
	os.Exit(1)
}

// secureZero zeros out sensitive data in memory (defense in depth)
func secureZero(b []byte) {
	for i := range b {
		b[i] = 0
	}
}

// readRandomBytes reads cryptographically secure random bytes
func readRandomBytes(n int) ([]byte, error) {
	b := make([]byte, n)
	if _, err := io.ReadFull(rand.Reader, b); err != nil {
		return nil, fmt.Errorf("failed to read random bytes: %w", err)
	}
	return b, nil
}
