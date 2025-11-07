use sc_cli::RunCmd;

#[derive(Debug, clap::Parser)]
pub struct Cli {
	#[command(subcommand)]
	pub subcommand: Option<Subcommand>,

	#[clap(flatten)]
	pub run: RunCmd,
}

#[derive(Debug, clap::Subcommand)]
pub enum Subcommand {
	/// Key management utilities
	#[command(subcommand)]
	Key(sc_cli::KeySubcommand),

	/// Build chain specification
	BuildSpec(sc_cli::BuildSpecCmd),

	/// Validate blocks
	CheckBlock(sc_cli::CheckBlockCmd),

	/// Export blocks
	ExportBlocks(sc_cli::ExportBlocksCmd),

	/// Export state
	ExportState(sc_cli::ExportStateCmd),

	/// Import blocks
	ImportBlocks(sc_cli::ImportBlocksCmd),

	/// Remove the whole chain
	PurgeChain(sc_cli::PurgeChainCmd),

	/// Revert the chain to a previous state
	Revert(sc_cli::RevertCmd),
}
