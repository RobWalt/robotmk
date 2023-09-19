use std::time::Instant;

pub struct Timeout {
    start_time: Instant,
    timeout: u64,
}

impl Timeout {
    pub fn start(timeout: u64) -> Self {
        Self {
            start_time: Instant::now(),
            timeout,
        }
    }

    pub fn expired(&self) -> bool {
        self.start_time.elapsed().as_secs() >= self.timeout
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_timout_expired() {
        assert!(Timeout::start(0).expired())
    }

    #[test]
    fn test_timout_not_expired() {
        assert!(!Timeout::start(10).expired())
    }
}
