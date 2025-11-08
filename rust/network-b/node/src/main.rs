// COINjecture Node
// Network B - NP-hard Consensus Blockchain

mod chain;
mod config;
mod genesis;
mod service;
mod validator;

use config::NodeConfig;
use service::CoinjectNode;
use tokio::signal;
use tokio::task::LocalSet;
use tracing_subscriber::EnvFilter;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging
    let filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new("info"));

    tracing_subscriber::fmt()
        .with_env_filter(filter)
        .with_target(false)
        .init();

    // Display banner
    print_banner();

    // Parse configuration
    let config = NodeConfig::parse_args();

    // Create LocalSet for spawn_local tasks
    let local = LocalSet::new();

    // Run node within LocalSet context
    local.run_until(async move {
        // Create and start node
        let mut node = CoinjectNode::new(config).await?;
        node.start().await?;

        // Wait for shutdown signal (Ctrl+C)
        match signal::ctrl_c().await {
            Ok(()) => {
                println!();
                println!("📡 Received shutdown signal (Ctrl+C)");
                node.shutdown();
            }
            Err(err) => {
                eprintln!("Unable to listen for shutdown signal: {}", err);
            }
        }

        // Wait for graceful shutdown
        node.wait_for_shutdown().await;

        println!("👋 COINjecture Node stopped");
        println!();

        Ok::<(), Box<dyn std::error::Error>>(())
    }).await
}

fn print_banner() {
    println!(r#"
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ██████╗ ██████╗ ██╗███╗   ██╗     ██╗███████╗ ██████╗████████╗███████╗██████╗   ║
    ║  ██╔════╝██╔═══██╗██║████╗  ██║     ██║██╔════╝██╔════╝╚══██╔══╝██╔════╝██╔══██╗  ║
    ║  ██║     ██║   ██║██║██╔██╗ ██║     ██║█████╗  ██║        ██║   █████╗  ██████╔╝  ║
    ║  ██║     ██║   ██║██║██║╚██╗██║██   ██║██╔══╝  ██║        ██║   ██╔══╝  ██╔══██╗  ║
    ║  ╚██████╗╚██████╔╝██║██║ ╚████║╚█████╔╝███████╗╚██████╗   ██║   ███████╗██║  ██║  ║
    ║   ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚════╝ ╚══════╝ ╚═════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝  ║
    ║                                                               ║
    ║                    Network B - NP-Hard Consensus              ║
    ║                    η = 1/√2 Tokenomics Engine                ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    "#);
    println!("    Version: {}", env!("CARGO_PKG_VERSION"));
    println!("    Repository: {}", env!("CARGO_PKG_REPOSITORY"));
    println!();
}
