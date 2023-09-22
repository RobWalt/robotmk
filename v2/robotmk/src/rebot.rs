use super::attempt::PYTHON_EXECUTABLE;
use super::command_spec::CommandSpec;
use super::environment::Environment;
use super::results::{RebotOutcome, RebotResult};

use anyhow::{Context, Result};
use base64::{engine::general_purpose, Engine};
use camino::{Utf8Path, Utf8PathBuf};
use log::debug;
use log::error;
use std::fs::{read, read_to_string};
use std::process::{Command, Output};

pub struct Rebot<'a> {
    pub environment: &'a Environment,
    pub input_paths: &'a [Utf8PathBuf],
    pub path_xml: &'a Utf8Path,
    pub path_html: &'a Utf8Path,
}

impl Rebot<'_> {
    pub fn rebot(&self) -> RebotOutcome {
        match self.run() {
            Ok(output) => {
                if output.status.success() {
                    self.process_successful_run()
                } else {
                    let rebot_run_stdout = String::from_utf8_lossy(&output.stdout);
                    let rebot_run_stderr = String::from_utf8_lossy(&output.stderr);
                    let error_message =
                        format!("Rebot run failed. Stdout:\n{rebot_run_stdout}\n\nStderr:\n{rebot_run_stderr}");
                    error!("{error_message}");
                    RebotOutcome::Error(error_message)
                }
            }
            Err(error) => {
                error!("Calling rebot command failed: {error:?}");
                RebotOutcome::Error(format!("{error:?}"))
            }
        }
    }

    fn run(&self) -> Result<Output> {
        let rebot_command_spec = self.environment.wrap(self.build_rebot_command_spec());
        debug!("Calling rebot command: {rebot_command_spec}");
        Command::from(&rebot_command_spec)
            .output()
            .context("Rebot command failed")
    }

    fn build_rebot_command_spec(&self) -> CommandSpec {
        let mut rebot_command_spec: CommandSpec = CommandSpec::new(PYTHON_EXECUTABLE);
        rebot_command_spec
            .add_argument("-m")
            .add_argument("robot.rebot")
            .add_argument("--output")
            .add_argument(self.path_xml)
            .add_argument("--log")
            .add_argument(self.path_html)
            .add_argument("--report")
            .add_argument("NONE")
            .add_arguments(self.input_paths);
        rebot_command_spec
    }

    fn process_successful_run(&self) -> RebotOutcome {
        match read_to_string(self.path_xml) {
            Ok(merged_xml) => match read(self.path_html) {
                Ok(merged_html) => RebotOutcome::Ok(RebotResult {
                    xml: merged_xml,
                    html_base64: general_purpose::STANDARD.encode(merged_html),
                }),
                Err(error) => {
                    let error_message = format!(
                        "Failed to read merged HTML file content from {}: {error:?}",
                        self.path_html
                    );
                    error!("{error_message}");
                    RebotOutcome::Error(error_message)
                }
            },
            Err(error) => {
                let error_message = format!(
                    "Failed to read merged XML file content from {}: {error:?}",
                    self.path_xml
                );
                error!("{error_message}");
                RebotOutcome::Error(error_message)
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::EnvironmentConfig;

    #[test]
    fn build_rebot_command() {
        let rebot_command_spec = Rebot {
            environment: &Environment::new("my_suite", &EnvironmentConfig::System),
            input_paths: &[
                Utf8PathBuf::from("/working/my_suite/0.xml"),
                Utf8PathBuf::from("/working/my_suite/1.xml"),
            ],
            path_xml: &Utf8PathBuf::from("/working/my_suite/rebot.xml"),
            path_html: &Utf8PathBuf::from("/working/my_suite/rebot.html"),
        }
        .build_rebot_command_spec();
        let mut expected = CommandSpec::new("python");
        expected
            .add_argument("-m")
            .add_argument("robot.rebot")
            .add_argument("--output")
            .add_argument("/working/my_suite/rebot.xml")
            .add_argument("--log")
            .add_argument("/working/my_suite/rebot.html")
            .add_argument("--report")
            .add_argument("NONE")
            .add_argument("/working/my_suite/0.xml")
            .add_argument("/working/my_suite/1.xml");
        assert_eq!(rebot_command_spec, expected)
    }
}