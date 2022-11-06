# marketresearch

This codebase contains tools to help market traders build trading strategies based on technical analysis. The following 
modules are currently included:

- clients: Contains code for interacting with various brokerage APIs.
- data: Contains untracked data files and the scripts for mining data from online services.


## Installation

0. After cloning, install anaconda on your machine.
0. In a terminal supporting anaconda commands, navigate on your local machine to this repo: 
`<path_to_repo>/marketresearch`
0. Install the conda environment by typing: `conda env create -f environment.yml`
0. Create the following untracked file: `marketresearch/marketresearch/clients/secrets.py`. This is where you should 
put credentials for online services. Alternatively, you can use this file as an interface to your credentials stored 
elsewhere on your machine.

## Use Cases
### Data Mining
```mermaid
%%{init: {'theme': 'default', 'themeVariables': { 'titleColor': '#0000FF', 'edgeLabelBackground': 'transparent'}}}%%
graph LR
    subgraph Mining[Data Mining]
        direction LR
        MiningAgent(Agent) -- <br>data request --> MiningClient(Client)
        MiningClient -- response packet<br><br> --> MiningAgent
        MiningAgent -- <br><br>valid response packet --> MiningDataView(DataView)
        MiningDataView -- <br>processed data --> MiningDatabase[(Database)]
    end
    style Mining color:#ffffde
```

### Backtesting
```mermaid
%%{init: {'theme': 'default', 'themeVariables': { 'titleColor': '#0000FF', 'edgeLabelBackground': 'transparent'}}}%%
graph RL
    subgraph Backtesting
    direction RL
        BacktestingAgent(Agent) -- <br>empty response packet --> BacktestingDataView(DataView)
        BacktestingDataView(DataView) -- processed data<br><br> --> BacktestingAgent
        BacktestingDatabase[(Database)] -. <br>access .-> BacktestingDataView
    end
    style Backtesting color:#ffffde
```

### Simulation
```mermaid
%%{init: {'theme': 'default', 'themeVariables': { 'titleColor': '#0000FF', 'edgeLabelBackground': 'transparent'}}}%%
graph RL
    subgraph Simulation
    direction RL
        SimulationAgent(Agent) -- <br><br><br>data request<br>trade order --> SimulationClient(Client)
        SimulationClient -- response packet<br><br><br> --> SimulationDataView(DataView)
        SimulationDataView -- processed data<br><br><br> --> SimulationAgent
        SimulationClient -- data request<br>trade order<br><br> --> SimulationMarket(Market)
        SimulationMarket -- <br>price action data<br>trade receipts --> SimulationClient
    end
    style Simulation color:#ffffde
```

### Algorithmic Trading
```mermaid
%%{init: {'theme': 'default', 'themeVariables': { 'titleColor': '#0000FF', 'edgeLabelBackground': 'transparent'}}}%%
graph LR
    subgraph AlgoTrading
    direction LR
        AlgoTradingAgent(Agent) -- <br><br>data request<br>trade order --> AlgoTradingClient(Client)
        AlgoTradingClient -- response packet<br><br> --> AlgoTradingAgent
        AlgoTradingAgent -- valid response packet<br><br> --> AlgoTradingDataView(DataView)
        AlgoTradingDataView -- <br>processed data --> AlgoTradingAgent
    end
    style AlgoTrading color:#ffffde
```
