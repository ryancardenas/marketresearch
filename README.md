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

## DataView Classes
```mermaid
classDiagram
    class AbstractDataView{
        +feeds: list~string~
        -feeds: dict~string:AbstractDataFeed~
        +update(): None
        +add_feed(): None
        -__getitem__(): None
    }

    class AbstractDataFeed{
        +name: string
        +data_type: type
        -data_source: AbstractDataBase
        +update(): None
        -connect_to_database(): None
    }
    
    class AbstractInstrument{
        +timeframes: list~string~
        -timeframes: dict~string:AbstractTimeframe~
        -initialize_timeframe_views(): None
        -__getitem__(): None
    }

    class AbstractTimeframe{
        +name: string
        +open: array~float~
        +high: array~float~ 
        +low: array~float~
        +close: array~float~ 
        +volume: array~int~
        +datetime: array~datetime64~
        +indicators: list~string~
        -indicators: dict~string:AbstractIndicator~
        -data_source: AbstractDataBase
        +update(): None
        -connect_to_database(): None
        -__getitem__(): None
    }

    class AbstractIndicator{
        +name: string
        +update(): None
    }

    class AbstractDataBase{
        +name: string
        +connect(): None
        +serve(): None
        +update(): None
    }

    class BacktestDataView{

    }

    class FxInstrument{

    }

    class FutureInstrument{
        <<not yet implemented>>
    }

    class StockInstrument{
        <<not yet implemented>>
    }

    class OptionInstrument{
        <<not yet implemented>>
    }

    class StockOptionInstrument{
        <<not yet implemented>>
    }

    class IndexOptionInstrument{
        <<not yet implemented>>
    }

    class StandardTimeframe{
        <<not yet implemented>>
    }

    class FxTimeframe{
        +spread: array~float~
        +tickvolume: array~int~
        +tradevolume: array~int~
        +swap: array~float~
    }

    AbstractDataView <|-- BacktestDataView
    AbstractDataView o-- AbstractDataFeed
    AbstractDataFeed <|-- AbstractInstrument
    AbstractDataFeed ..> AbstractDataBase
    AbstractDataBase <.. AbstractTimeframe
    AbstractInstrument *-- AbstractTimeframe
    AbstractTimeframe *-- AbstractIndicator
    AbstractInstrument <|-- OptionInstrument
    AbstractInstrument <|-- FxInstrument
    AbstractInstrument <|-- FutureInstrument
    AbstractInstrument <|-- StockInstrument
    OptionInstrument <|-- StockOptionInstrument
    OptionInstrument <|-- IndexOptionInstrument
    AbstractTimeframe <|-- FxTimeframe
    AbstractTimeframe <|-- StandardTimeframe


```