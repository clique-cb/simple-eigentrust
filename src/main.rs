use std::path;
use std::io::{Write, Result};
use clap::Parser;
use ndarray::Array;

use crate::io::{get_buffered_reader, get_buffered_writer, whitespace_split, next_val};

pub mod io;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Args {
    // Read from file (otherwise from stdin)
    #[arg(short, long, value_name = "FILE")]
    input_file: Option<path::PathBuf>,

    // Write to file (otherwise to stdout)
    #[arg(short, long, value_name = "FILE")]    
    output_file: Option<path::PathBuf>,
}



fn main() -> Result<()> {
    let args = Args::parse();
    let reader = get_buffered_reader(&args.input_file)?;
    let mut writer = get_buffered_writer(&args.output_file)?;

    let words = &mut whitespace_split(reader);
    let n: usize = next_val(words)?;
    let m: usize = next_val(words)?;

    let mut G = Array::zeros((n, n));

    for _i in 0..m {
        let u: usize = next_val(words)?;
        let v: usize = next_val(words)?;
        let w: f32 = next_val(words)?;
        
        G[[u, v]] = w
    }

    let mut p = Array::zeros(n);

    for i in 0..n {
        let pi: f32 = next_val(words)?;
        p[i] = pi;    
    }

    for i in 0..n {
        for j in 0..n {
            write!(writer, "{} ", G[[i, j]])?;
        }
        write!(writer, "\n")?;
    }

    Ok(())
}
