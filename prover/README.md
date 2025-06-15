# ZK Proof System for Arbitrage Verification

This directory contains the Zero-Knowledge proof system used to verify arbitrage opportunities without revealing sensitive strategy details.

## Files

- `circuit.circom`: The circuit definition in Circom language
- `circuit.wasm`: WebAssembly compiled version of the circuit
- `circuit_final.zkey`: The proving key for the circuit
- `generate_witness.js`: Script to generate a witness for the circuit

## Usage

### Prerequisites

Install the required dependencies:

```bash
npm install snarkjs
```

### Generating a Proof

1. Create an input file (e.g., `input.json`) with the required parameters:

```json
{
  "pnl": 12345,
  "model_id": 1
}
```

2. Generate a witness:

```bash
node generate_witness.js input.json witness.wtns
```

3. Generate a proof:

```bash
snarkjs groth16 prove circuit_final.zkey witness.wtns proof.json public.json
```

4. Verify the proof:

```bash
snarkjs groth16 verify verification_key.json public.json proof.json
```

## Testnet vs Mainnet

For testnet usage, you can use the provided mock files. For mainnet deployment:

1. Generate a proper circuit using Circom
2. Compile the circuit to WebAssembly
3. Generate a proper zkey file with a secure trusted setup
4. Update the verification contract with the correct verification key