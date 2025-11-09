// COINjecture Network B Wallet CLI
// Interactive command-line wallet for managing accounts, transactions, and marketplace interactions

use clap::{Parser, Subcommand};
use colored::*;

mod commands;
mod keystore;
mod rpc_client;

use commands::{account, marketplace, transaction};
use rpc_client::RpcClient;

/// COINjecture Network B Wallet CLI
#[derive(Parser)]
#[command(name = "coinject-wallet")]
#[command(version = "0.1.0")]
#[command(about = "Command-line wallet for COINjecture Network B", long_about = None)]
struct Cli {
    /// RPC endpoint URL
    #[arg(short, long, default_value = "http://127.0.0.1:9944")]
    rpc: String,

    /// Verbose output
    #[arg(short, long)]
    verbose: bool,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Account management commands
    #[command(subcommand)]
    Account(AccountCommands),

    /// Transaction commands
    #[command(subcommand)]
    Transaction(TransactionCommands),

    /// Marketplace commands
    #[command(subcommand)]
    Marketplace(MarketplaceCommands),

    /// Chain information commands
    #[command(subcommand)]
    Chain(ChainCommands),
}

#[derive(Subcommand)]
enum AccountCommands {
    /// Generate a new keypair
    New {
        /// Name for the account
        #[arg(short, long)]
        name: Option<String>,
    },

    /// List all accounts in keystore
    List,

    /// Get account balance
    Balance {
        /// Account address (hex)
        address: String,
    },

    /// Get full account information
    Info {
        /// Account address (hex)
        address: String,
    },

    /// Export account private key
    Export {
        /// Account name or address
        account: String,
    },

    /// Import account from private key
    Import {
        /// Private key (hex)
        #[arg(short, long)]
        key: String,

        /// Name for the account
        #[arg(short, long)]
        name: Option<String>,
    },
}

#[derive(Subcommand)]
enum TransactionCommands {
    /// Send tokens to an address
    Send {
        /// Sender account name or address
        #[arg(short, long)]
        from: String,

        /// Recipient address
        to: String,

        /// Amount to send
        amount: u128,
    },

    /// Create a time-locked transaction
    Timelock {
        /// Sender account name or address
        #[arg(short, long)]
        from: String,

        /// Recipient address (who can claim after unlock)
        to: String,

        /// Amount to lock
        amount: u128,

        /// Unlock time in seconds from now (e.g., 3600 for 1 hour)
        #[arg(short, long)]
        unlock_in: i64,
    },

    /// Get transaction status
    Status {
        /// Transaction hash (hex)
        tx_hash: String,
    },
}

#[derive(Subcommand)]
enum MarketplaceCommands {
    /// List open problems
    ListProblems,

    /// Get marketplace statistics
    Stats,

    /// Get problem details
    Problem {
        /// Problem ID (hex)
        problem_id: String,
    },

    /// Submit a new problem (requires implementation)
    Submit {
        /// Problem type (sat, tsp, subsetsum)
        #[arg(short, long)]
        problem_type: String,

        /// Bounty amount
        #[arg(short, long)]
        bounty: u128,
    },
}

#[derive(Subcommand)]
enum ChainCommands {
    /// Get chain information
    Info,

    /// Get block by height
    Block {
        /// Block height
        height: u64,
    },

    /// Get latest block
    Latest,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    // Print banner
    print_banner();

    // Create RPC client
    let client = RpcClient::new(&cli.rpc);

    if cli.verbose {
        println!("{}", format!("🔌 Connected to: {}", cli.rpc).dimmed());
        println!();
    }

    // Route to appropriate command handler
    match cli.command {
        Commands::Account(cmd) => handle_account_command(cmd, &client).await?,
        Commands::Transaction(cmd) => handle_transaction_command(cmd, &client).await?,
        Commands::Marketplace(cmd) => handle_marketplace_command(cmd, &client).await?,
        Commands::Chain(cmd) => handle_chain_command(cmd, &client).await?,
    }

    Ok(())
}

async fn handle_account_command(cmd: AccountCommands, client: &RpcClient) -> anyhow::Result<()> {
    match cmd {
        AccountCommands::New { name } => account::new_account(name).await?,
        AccountCommands::List => account::list_accounts().await?,
        AccountCommands::Balance { address } => account::get_balance(&address, client).await?,
        AccountCommands::Info { address } => account::get_account_info(&address, client).await?,
        AccountCommands::Export { account } => account::export_account(&account).await?,
        AccountCommands::Import { key, name } => account::import_account(&key, name).await?,
    }
    Ok(())
}

async fn handle_transaction_command(
    cmd: TransactionCommands,
    client: &RpcClient,
) -> anyhow::Result<()> {
    match cmd {
        TransactionCommands::Send { from, to, amount } => {
            transaction::send_tokens(&from, &to, amount, client).await?
        }
        TransactionCommands::Timelock { from, to, amount, unlock_in } => {
            transaction::create_timelock(&from, &to, amount, unlock_in, client).await?
        }
        TransactionCommands::Status { tx_hash } => {
            transaction::get_transaction_status(&tx_hash, client).await?
        }
    }
    Ok(())
}

async fn handle_marketplace_command(
    cmd: MarketplaceCommands,
    client: &RpcClient,
) -> anyhow::Result<()> {
    match cmd {
        MarketplaceCommands::ListProblems => marketplace::list_problems(client).await?,
        MarketplaceCommands::Stats => marketplace::get_stats(client).await?,
        MarketplaceCommands::Problem { problem_id } => {
            marketplace::get_problem(&problem_id, client).await?
        }
        MarketplaceCommands::Submit {
            problem_type,
            bounty,
        } => marketplace::submit_problem(&problem_type, bounty, client).await?,
    }
    Ok(())
}

async fn handle_chain_command(cmd: ChainCommands, client: &RpcClient) -> anyhow::Result<()> {
    match cmd {
        ChainCommands::Info => {
            let info = client.get_chain_info().await?;
            println!("{}", "Chain Information".green().bold());
            println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            println!("Chain ID:      {}", info.chain_id);
            println!("Best Height:   {}", info.best_height);
            println!("Best Hash:     {}", info.best_hash);
            println!("Genesis Hash:  {}", info.genesis_hash);
            println!("Peers:         {}", info.peer_count);
        }
        ChainCommands::Block { height } => {
            if let Some(block) = client.get_block(height).await? {
                println!("{}", format!("Block #{}", height).green().bold());
                println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                println!("Hash:       {}", hex::encode(block.header.hash().as_bytes()));
                println!(
                    "Parent:     {}",
                    hex::encode(block.header.prev_hash.as_bytes())
                );
                println!("Miner:      {}", hex::encode(block.header.miner.as_bytes()));
                println!("Timestamp:  {}", block.header.timestamp);
                println!("Nonce:      {}", block.header.nonce);
                println!();
                println!("Problem:    {:?}", block.solution_reveal.problem);
                println!("Solution:   {:?}", block.solution_reveal.solution);
                println!("Work Score: {:.4}", block.header.work_score);
                println!("Reward:     {} tokens", block.coinbase.reward);
            } else {
                println!("{}", "Block not found".red());
            }
        }
        ChainCommands::Latest => {
            if let Some(block) = client.get_latest_block().await? {
                let height = block.header.height;
                println!("{}", format!("Latest Block #{}", height).green().bold());
                println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                println!("Hash:       {}", hex::encode(block.header.hash().as_bytes()));
                println!("Miner:      {}", hex::encode(block.header.miner.as_bytes()));
                println!("Timestamp:  {}", block.header.timestamp);
                println!("Work Score: {:.4}", block.header.work_score);
                println!("Reward:     {} tokens", block.coinbase.reward);
            } else {
                println!("{}", "No blocks found".red());
            }
        }
    }
    Ok(())
}

fn print_banner() {
    println!("{}", "╔═══════════════════════════════════════════════════════════════╗".cyan());
    println!("{}", "║                                                               ║".cyan());
    println!("{}", "║   ██████╗ ██████╗ ██╗███╗   ██╗     ██╗███████╗ ██████╗████████╗███████╗██████╗   ║".cyan());
    println!("{}", "║  ██╔════╝██╔═══██╗██║████╗  ██║     ██║██╔════╝██╔════╝╚══██╔══╝██╔════╝██╔══██╗  ║".cyan());
    println!("{}", "║  ██║     ██║   ██║██║██╔██╗ ██║     ██║█████╗  ██║        ██║   █████╗  ██████╔╝  ║".cyan());
    println!("{}", "║  ██║     ██║   ██║██║██║╚██╗██║██   ██║██╔══╝  ██║        ██║   ██╔══╝  ██╔══██╗  ║".cyan());
    println!("{}", "║  ╚██████╗╚██████╔╝██║██║ ╚████║╚█████╔╝███████╗╚██████╗   ██║   ███████╗██║  ██║  ║".cyan());
    println!("{}", "║   ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚════╝ ╚══════╝ ╚═════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝  ║".cyan());
    println!("{}", "║                                                               ║".cyan());
    println!("{}", "║                    Network B Wallet CLI v0.1.0                ║".cyan());
    println!("{}", "║                    NP-Hard Consensus • η=1/√2                 ║".cyan());
    println!("{}", "║                                                               ║".cyan());
    println!("{}", "╚═══════════════════════════════════════════════════════════════╝".cyan());
    println!();
}
