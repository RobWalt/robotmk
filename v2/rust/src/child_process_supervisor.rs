use super::termination::TerminationFlag;
use super::timeout::Timeout;
use anyhow::{bail, Context, Result};
use log::{error, warn};
use std::collections::{HashMap, HashSet};
use std::process::{Child, Command, ExitStatus};
use std::thread::sleep;
use std::time::Duration;
use sysinfo::{Pid, PidExt, Process, ProcessExt, System, SystemExt};

pub struct ChildProcessSupervisor<'a> {
    pub command: Command,
    pub timeout: u64,
    pub termination_flag: &'a TerminationFlag,
}

impl ChildProcessSupervisor<'_> {
    pub fn run(mut self) -> Result<ChildProcessOutcome> {
        let mut child = self.command.spawn().context("Failed to spawn subprocess")?;
        let timeout = Timeout::start(self.timeout);

        loop {
            if let Some(exit_status) = child
                .try_wait()
                .context(format!(
                    "Failed to query exit status of process {}, killing",
                    child.id()
                ))
                .map_err(|err| {
                    kill_child_process_tree(&mut child);
                    err
                })?
            {
                return Ok(ChildProcessOutcome::Exited(exit_status));
            }

            if timeout.expired() {
                error!("Process timed out");
                kill_child_process_tree(&mut child);
                return Ok(ChildProcessOutcome::TimedOut);
            }

            if self.termination_flag.should_terminate() {
                warn!("Terminated");
                kill_child_process_tree(&mut child);
                bail!("Terminated")
            }
            sleep(Duration::from_millis(250))
        }
    }
}

pub enum ChildProcessOutcome {
    Exited(ExitStatus),
    TimedOut,
}

fn kill_child_process_tree(child: &mut Child) {
    let mut system = System::new_all();
    system.refresh_processes();
    let _ = child.kill();
    kill_all_children(&Pid::from_u32(child.id()), system.processes());
}

fn kill_all_children<'a>(top_pid: &'a Pid, processes: &'a HashMap<Pid, Process>) {
    let mut pids_in_tree = HashSet::from([top_pid]);

    loop {
        let current_tree_size = pids_in_tree.len();
        add_and_kill_direct_children(&mut pids_in_tree, processes);
        if pids_in_tree.len() == current_tree_size {
            break;
        }
    }
}

fn add_and_kill_direct_children<'a>(
    pids_in_tree: &mut HashSet<&'a Pid>,
    processes: &'a HashMap<Pid, Process>,
) {
    for (pid, parent_pid, process) in processes.iter().filter_map(|(pid, process)| {
        process
            .parent()
            .map(|parent_pid| (pid, parent_pid, process))
    }) {
        {
            if pids_in_tree.contains(&parent_pid) {
                pids_in_tree.insert(pid);
                process.kill();
            }
        }
    }
}
