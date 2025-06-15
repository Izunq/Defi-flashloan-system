#!/usr/bin/env python3
# =================================================================================================
# ENHANCED ZK PROOF GENERATION AND VERIFICATION
# =================================================================================================

import os
import json
import subprocess
import argparse
import logging
import time
import hashlib
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from cryptography.exceptions import InvalidSignature

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("zk_proof.log")
    ]
)
logger = logging.getLogger("ZKProofGenerator")

# Constants
PROVER_DIR = os.path.join(os.getcwd(), "prover")
CIRCUIT_FINAL_ZKEY = os.path.join(PROVER_DIR, "circuit_final.zkey")
VERIFICATION_KEY_PATH = os.path.join(PROVER_DIR, "verification_key.json")
WITNESS_GENERATOR = os.path.join(PROVER_DIR, "generate_witness.js")
API_URL = os.environ.get("API_URL", "http://localhost:8080")
API_KEY = os.environ.get("API_KEY", "test-api-key")

class ZKProofGenerator:
    """Enhanced ZK Proof Generator with verification capabilities"""
    
    def __init__(self):
        """Initialize the ZK Proof Generator"""
        self._check_dependencies()
        self._load_verification_key()
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
    
    def _check_dependencies(self) -> None:
        """Check if all required dependencies are available"""
        # Check if prover directory exists
        if not os.path.exists(PROVER_DIR):
            raise FileNotFoundError(f"Prover directory does not exist: {PROVER_DIR}")
        
        # Check if witness generator exists
        if not os.path.exists(WITNESS_GENERATOR):
            raise FileNotFoundError(f"Witness generator does not exist: {WITNESS_GENERATOR}")
        
        # Check if circuit zkey exists
        if not os.path.exists(CIRCUIT_FINAL_ZKEY):
            raise FileNotFoundError(f"Circuit zkey does not exist: {CIRCUIT_FINAL_ZKEY}")
        
        # Check if snarkjs is installed
        try:
            subprocess.run(["snarkjs", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("snarkjs is not installed or not in PATH")
        
        # Check if node is installed
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("node is not installed or not in PATH")
    
    def _load_verification_key(self) -> None:
        """Load the verification key"""
        try:
            with open(VERIFICATION_KEY_PATH, 'r') as f:
                self.verification_key = json.load(f)
            logger.info("Verification key loaded successfully")
        except FileNotFoundError:
            logger.warning(f"Verification key not found at {VERIFICATION_KEY_PATH}")
            self.verification_key = None
    
    def generate_proof(self, 
                      strategy_id: int, 
                      profit_usd: float, 
                      intelligence_score: int = 75) -> Dict[str, Any]:
        """
        Generate a ZK proof for a strategy
        
        Args:
            strategy_id: ID of the strategy
            profit_usd: Profit in USD
            intelligence_score: Intelligence score (0-100)
            
        Returns:
            Dict containing the proof and public inputs
        """
        logger.info(f"Generating ZK proof for strategy {strategy_id} with profit=${profit_usd:.2f}")
        
        # Prepare inputs
        inputs = {
            "strategyId": strategy_id,
            "pnl": int(profit_usd * 100),  # Convert to cents
            "intelligenceScore": intelligence_score
        }
        
        # Paths
        inputs_path = os.path.join(PROVER_DIR, "input.json")
        witness_path = os.path.join(PROVER_DIR, "witness.wtns")
        proof_path = os.path.join(PROVER_DIR, "proof.json")
        public_path = os.path.join(PROVER_DIR, "public.json")
        
        # Write inputs to file
        with open(inputs_path, 'w') as f:
            json.dump(inputs, f)
        
        try:
            # Step 1: Generate witness
            logger.info("Generating witness...")
            witness_cmd = ["node", WITNESS_GENERATOR, inputs_path, witness_path]
            subprocess.run(witness_cmd, check=True, capture_output=True)
            
            # Step 2: Generate proof
            logger.info("Generating proof...")
            proof_cmd = ["snarkjs", "groth16", "prove", CIRCUIT_FINAL_ZKEY, witness_path, proof_path, public_path]
            subprocess.run(proof_cmd, check=True, capture_output=True)
            
            # Step 3: Load proof and public inputs
            with open(proof_path, 'r') as f:
                proof = json.load(f)
            with open(public_path, 'r') as f:
                public_inputs = json.load(f)
            
            # Step 4: Verify the proof locally
            verify_cmd = ["snarkjs", "groth16", "verify", VERIFICATION_KEY_PATH, public_path, proof_path]
            verify_result = subprocess.run(verify_cmd, check=True, capture_output=True)
            
            is_valid = "OK" in verify_result.stdout.decode()
            
            if not is_valid:
                logger.error("Proof verification failed")
                raise ValueError("Generated proof is not valid")
            
            logger.info("Proof generated and verified successfully!")
            
            # Step 5: Format the result
            result = {
                "strategyId": strategy_id,
                "publicInputs": public_inputs,
                "proof": proof,
                "timestamp": int(time.time()),
                "isValid": is_valid
            }
            
            # Step 6: Sign the proof
            result["signature"] = self._sign_proof(result)
            
            return result
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Process error: {e}")
            logger.error(f"Stdout: {e.stdout.decode() if e.stdout else 'None'}")
            logger.error(f"Stderr: {e.stderr.decode() if e.stderr else 'None'}")
            raise RuntimeError(f"Error generating proof: {e}")
        
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    def _sign_proof(self, proof_data: Dict[str, Any]) -> str:
        """
        Sign the proof data
        
        Args:
            proof_data: Proof data to sign
            
        Returns:
            Signature as a hex string
        """
        # Create a deterministic representation of the proof data
        data_to_sign = json.dumps(proof_data, sort_keys=True).encode()
        
        # Hash the data
        digest = hashlib.sha256(data_to_sign).digest()
        
        # Sign the hash
        signature = self.private_key.sign(
            digest,
            ec.ECDSA(hashes.SHA256())
        )
        
        # Convert to hex
        r, s = encode_dss_signature(signature)
        return f"{r.to_bytes(32, 'big').hex()}{s.to_bytes(32, 'big').hex()}"
    
    def verify_signature(self, proof_data: Dict[str, Any], signature: str) -> bool:
        """
        Verify the signature of proof data
        
        Args:
            proof_data: Proof data that was signed
            signature: Signature to verify
            
        Returns:
            True if signature is valid, False otherwise
        """
        # Create a copy of the proof data without the signature
        data_to_verify = {k: v for k, v in proof_data.items() if k != "signature"}
        
        # Create a deterministic representation of the proof data
        data_bytes = json.dumps(data_to_verify, sort_keys=True).encode()
        
        # Hash the data
        digest = hashlib.sha256(data_bytes).digest()
        
        # Parse the signature
        r_bytes = bytes.fromhex(signature[:64])
        s_bytes = bytes.fromhex(signature[64:])
        
        r = int.from_bytes(r_bytes, 'big')
        s = int.from_bytes(s_bytes, 'big')
        
        signature_bytes = encode_dss_signature(r, s)
        
        try:
            # Verify the signature
            self.public_key.verify(
                signature_bytes,
                digest,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except InvalidSignature:
            return False
    
    def submit_proof_to_api(self, proof_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit the proof to the API
        
        Args:
            proof_data: Proof data to submit
            
        Returns:
            API response
        """
        logger.info(f"Submitting proof for strategy {proof_data['strategyId']} to API")
        
        try:
            # Prepare the request data
            request_data = {
                "strategyId": proof_data["strategyId"],
                "publicInputs": proof_data["publicInputs"],
                "proof": json.dumps(proof_data["proof"]),
                "signature": proof_data["signature"]
            }
            
            # Send the request
            response = requests.post(
                f"{API_URL}/api/zk/submit",
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": API_KEY
                },
                timeout=30
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            logger.info(f"Proof submitted successfully: {result}")
            
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error submitting proof to API: {e}")
            raise
    
    def verify_proof_on_chain(self, proof_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify the proof on-chain
        
        Args:
            proof_data: Proof data to verify
            
        Returns:
            Verification result
        """
        logger.info(f"Verifying proof for strategy {proof_data['strategyId']} on-chain")
        
        try:
            # Prepare the request data
            request_data = {
                "strategyId": proof_data["strategyId"],
                "publicInputs": proof_data["publicInputs"],
                "proof": json.dumps(proof_data["proof"])
            }
            
            # Send the request
            response = requests.post(
                f"{API_URL}/api/zk/verify",
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": API_KEY
                },
                timeout=60  # Longer timeout for on-chain verification
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            logger.info(f"Proof verified on-chain: {result}")
            
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error verifying proof on-chain: {e}")
            raise

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="ZK Proof Generation and Verification")
    parser.add_argument("--strategy-id", type=int, default=1, help="Strategy ID")
    parser.add_argument("--profit", type=float, default=100.0, help="Profit in USD")
    parser.add_argument("--intelligence", type=int, default=75, help="Intelligence score (0-100)")
    parser.add_argument("--submit", action="store_true", help="Submit proof to API")
    parser.add_argument("--verify", action="store_true", help="Verify proof on-chain")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("ZK PROOF GENERATION AND VERIFICATION")
    print("=" * 80)
    
    try:
        # Initialize the ZK proof generator
        zk_generator = ZKProofGenerator()
        
        # Generate the proof
        proof_data = zk_generator.generate_proof(
            args.strategy_id,
            args.profit,
            args.intelligence
        )
        
        print("\n✅ ZK proof generation PASSED")
        
        # Verify the signature
        if zk_generator.verify_signature(proof_data, proof_data["signature"]):
            print("✅ Signature verification PASSED")
        else:
            print("❌ Signature verification FAILED")
        
        # Submit the proof to the API
        if args.submit:
            try:
                submission_result = zk_generator.submit_proof_to_api(proof_data)
                print(f"\n✅ Proof submission PASSED: {submission_result}")
            except Exception as e:
                print(f"\n❌ Proof submission FAILED: {e}")
        
        # Verify the proof on-chain
        if args.verify:
            try:
                verification_result = zk_generator.verify_proof_on_chain(proof_data)
                print(f"\n✅ On-chain verification PASSED: {verification_result}")
            except Exception as e:
                print(f"\n❌ On-chain verification FAILED: {e}")
        
    except Exception as e:
        print(f"\n❌ ZK proof generation FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()