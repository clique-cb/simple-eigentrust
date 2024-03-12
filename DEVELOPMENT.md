EigenLightning
===

Lightning-like payment system (and furthermore - a system for uncollateralized debt provisioning) which reuses native ETH stakes as collateral for node operators.

## Core protocol development

- Public layer
  - Contract which stores the entirety of the graph
  - Supports `setCaps` + `setFlows` + `deposit` + `withdraw`.
    - `setFlows` implements batch settlement
  - Off-chain layer:
    - Simple routing on public graph
    - Peer-to-peer network addressing and discovery
       - Kademlia DHT?
       - Or maybe just __onion routing__?
         - Onion encryption using ECDSA pubkeys
         - __Garlic routing__ is an easy extension
       - How to ensure connectivity with neighbors if their IPs are non-static?
    
  - Transaction fees
    - Protocol fees
      - Which assets to use
        - ETH only?
        - What about token transactions?
      - How to make sure that the fee corresponds to the actual volume transferred?
        - Optimistic approach (fraud proofs with tx receipt from the node?)
        - ZK approach (small malleable proofs aggregating into big one?)
    
    - Validator fees
      - How do validators publish the fee rates?
        - Constant fee + percentage?
        - How the fee for edge transfer is split between two validators?
      - How the fee is paid exactly?
        - Deductions in the sum along the way
          - Part of "unwrapping" in garlic routing?
      - How to make sure they charge exactly as advertised?
        - Fraud proofs for over-charging?
        - Who publishes the fraud proof?
        - How to avoid the transaction being stopped along the way?


## EigenLayer

- Contract development
  - Main question: programmability of slashing
  - https://github.com/Layr-Labs/eigenlayer-contracts/tree/master#introduction
  - https://www.blog.eigenlayer.xyz/ycie/

- Off-chain code development
  - Go framework (non-finished): https://github.com/Layr-Labs/eigensdk-go
  - Can we avoid Go? maybe Rust?

## Ligntning Network

- Merging the concepts of Clique protocol and Lightning Network
  - Using undirected graphs
    - How the protocol invariants change for ZK implementation?
    - How does _borrowing_ change the network dynamics?
  - How do fees work in Lightning?

