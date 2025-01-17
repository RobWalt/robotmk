use clap::{ArgAction, Parser};
use flexi_logger::LogSpecification;
use std::path::PathBuf;

#[derive(Parser)]
#[command(about = "Robotmk suite scheduler.")]
pub struct Args {
    /// Configuration file path.
    #[arg(name = "CONFIG_PATH")]
    pub config_path: PathBuf,

    /// Log file path. If left unspecified, the program will log to standard error.
    #[arg(long, name = "LOG_PATH")]
    pub log_path: Option<PathBuf>,

    /// Enable verbose output. Use once (-v) for logging level INFO and twice (-vv) for logging
    /// level DEBUG.
    #[arg(short, long, action = ArgAction::Count)]
    verbose: u8,
}

impl Args {
    pub fn log_specification(&self) -> LogSpecification {
        match self.verbose {
            2.. => LogSpecification::debug(),
            1 => LogSpecification::info(),
            _ => LogSpecification::warn(),
        }
    }
}
