use anyhow::{Context, Result};
use atomicwrites::replace_atomic;
use std::collections::HashSet;
use std::fs::{create_dir_all, read_dir, remove_file};
use std::path::{Path, PathBuf};

use super::config::Config;
use super::environment::environment_building_stdio_directory;
use super::results::{suite_result_file, suite_results_directory};

pub fn setup(config: &Config) -> Result<()> {
    create_dir_all(&config.working_directory).context("Failed to create working directory")?;
    create_dir_all(environment_building_stdio_directory(
        &config.working_directory,
    ))
    .context("Failed to create environment building stdio directory")?;
    create_dir_all(&config.results_directory).context("Failed to create results directory")?;
    create_dir_all(suite_results_directory(&config.results_directory))
        .context("Failed to create suite results directory")?;
    clean_up_results_directory_atomic(config)
}

fn clean_up_results_directory_atomic(config: &Config) -> Result<()> {
    let suite_results_directory = suite_results_directory(&config.results_directory);
    let result_files_to_keep = config
        .suites()
        .into_iter()
        .map(|(suite_name, _suite_config)| suite_result_file(&suite_results_directory, suite_name));
    let currently_present_result_files = currently_present_result_files(&suite_results_directory)?;
    remove_files_atomic(
        &suite_results_directory.join("deprecated_result"),
        HashSet::<PathBuf>::from_iter(currently_present_result_files)
            .difference(&HashSet::from_iter(result_files_to_keep)),
    )
}

fn currently_present_result_files(suite_results_directory: &Path) -> Result<Vec<PathBuf>> {
    let mut result_files = vec![];

    for dir_entry in read_dir(suite_results_directory).context(format!(
        "Failed to read entries of results directory {}",
        suite_results_directory.display()
    ))? {
        let dir_entry = dir_entry.context(format!(
            "Failed to read entries of results directory {}",
            suite_results_directory.display()
        ))?;
        if dir_entry
            .file_type()
            .context(format!(
                "Failed to determine file type of {}",
                dir_entry.path().display()
            ))?
            .is_file()
        {
            result_files.push(dir_entry.path())
        }
    }

    Ok(result_files)
}

fn remove_files_atomic<'a>(
    intermediate_path_for_move: &Path,
    files_to_be_removed: impl Iterator<Item = &'a PathBuf>,
) -> Result<()> {
    for path in files_to_be_removed {
        replace_atomic(path, intermediate_path_for_move).context(format!(
            "Failed to move {} to {}",
            path.display(),
            intermediate_path_for_move.display()
        ))?;
    }

    let _ = remove_file(intermediate_path_for_move);

    Ok(())
}
