use std::{io, path};
use std::io::{BufReader, BufWriter, BufRead, Write, Result, Lines, Error, ErrorKind};
use std::error::Error as ErrorT;
use std::collections::VecDeque;
use std::fs::File;
use std::str::FromStr;

pub struct WhitespaceSplit<B> {
    lines: Lines<B>,
    cur_split: VecDeque<String>,
}


impl<B: BufRead> Iterator for WhitespaceSplit<B> {
    type Item = Result<String>;

    fn next(&mut self) -> Option<Result<String>> {
        loop {
            if self.cur_split.len() == 0 {
                let line = self.lines.next()?.unwrap();
                let mut split = line.split(' ').map(|w| w.to_string()).collect();
                self.cur_split.append(&mut split);
            }

            match self.cur_split.pop_front() {
                Some(s) => return Some(Ok(s)),
                None => continue,
            }
        }
    }
}

pub fn get_buffered_reader(path: &Option<path::PathBuf>) -> Result<Box<dyn BufRead>> {
    match path {
        Some(path) => {
            let f = File::open(path)?;
            Ok(Box::new(BufReader::new(f)))
        }
        None => Ok(Box::new(io::stdin().lock())),
    }
}

pub fn get_buffered_writer(path: &Option<path::PathBuf>) -> Result<Box<dyn Write>> {
    match path {
        Some(path) => {
            let f = File::open(path)?;
            Ok(Box::new(BufWriter::new(f)))
        }
        None => Ok(Box::new(BufWriter::new(io::stdout()))),
    }
}

pub fn whitespace_split<B: BufRead>(buf: B) -> WhitespaceSplit<B> {
    WhitespaceSplit { lines: buf.lines(), cur_split: VecDeque::new() }
}

pub fn next_val<B: BufRead, V: FromStr>(ws: &mut WhitespaceSplit<B>) -> Result<V>
    where <V as FromStr>::Err: ErrorT + Send + Sync + 'static
{
    let w: String = ws.next().unwrap()?;
    w.parse().map_err(|e| Error::new(ErrorKind::InvalidData, e))
}