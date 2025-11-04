# Creating Class and Sequence Diagrams for NemoSDK

This guide explains multiple approaches to create UML class diagrams and sequence diagrams for the NemoSDK project.

## Overview

The NemoSDK has the following main components:

### Main Classes (from `nemosdk/model.py`)
- `BIUNetworkDefaults`: Global network configuration defaults
- `Synapses`: Synapse connection matrix
- `NeuronOverrideRange`: Per-neuron range overrides
- `NeuronOverride`: Single neuron overrides
- `Layer`: Network layer definition

### Main Classes (from `nemosdk/compiler.py`)
- `CompiledModel`: Wrapper for compiled model artifacts

### Main Classes (from `nemosdk/runner.py`)
- `NemoSimRunner`: Simulator execution runner
- `RunResult`: Execution result summary

## Method 1: Using pyreverse (PyUML) - Automated Class Diagrams

`pyreverse` (part of pylint) can automatically generate class diagrams from Python code.

### Installation
```bash
pip install pylint
```

### Generate Class Diagrams
```bash
# Generate class diagram for the entire nemosdk package
pyreverse -o png -p NemoSDK nemosdk/

# Or generate as Graphviz DOT file (more control)
pyreverse -o dot -p NemoSDK nemosdk/
dot -Tpng classes_NemoSDK.dot -o class_diagram.png

# Generate separate diagrams for each module
pyreverse -o png nemosdk/model.py
pyreverse -o png nemosdk/compiler.py
pyreverse -o png nemosdk/runner.py
```

## Method 2: Using PlantUML - Text-Based Diagrams

PlantUML uses text-based syntax to generate diagrams. Great for version control.

### Installation
```bash
# Option 1: Java-based (requires Java)
# Download from https://plantuml.com/download
java -jar plantuml.jar diagram.puml

# Option 2: Python package (wrapper)
pip install plantuml
```

### Create Class Diagram (`docs/diagrams/class_diagram.puml`)
```plantuml
@startuml NemoSDK_Class_Diagram

package "nemosdk.model" {
  class BIUNetworkDefaults {
    +VTh: Optional[float]
    +RLeak: Optional[float]
    +refractory: Optional[int]
    +VDD: Optional[float]
    +Cn: Optional[float]
    +Cu: Optional[float]
    +fclk: Optional[float]
    +DSBitWidth: Optional[int]
    +DSClockMHz: Optional[float]
    +DSMode: Optional[str]
    +validate(): None
  }

  class Synapses {
    +rows: int
    +cols: int
    +weights: List[List[float]]
    +validate(): None
  }

  class NeuronOverrideRange {
    +start: int
    +end: int
    +VTh: Optional[float]
    +RLeak: Optional[float]
    +refractory: Optional[int]
    +validate(layer_size: int): None
  }

  class NeuronOverride {
    +index: int
    +VTh: Optional[float]
    +RLeak: Optional[float]
    +refractory: Optional[int]
    +validate(layer_size: int): None
  }

  class Layer {
    +size: int
    +synapses: Synapses
    +ranges: List[NeuronOverrideRange]
    +neurons: List[NeuronOverride]
    +validate(): None
  }
}

package "nemosdk.compiler" {
  class CompiledModel {
    -config_path: Path
    +get_config_path(): Path
  }
  
  note right of CompiledModel
    Wrapper for compiled
    model artifacts
  end note
}

package "nemosdk.runner" {
  class NemoSimRunner {
    -working_dir: Path
    -binary_path: Path
    +run(config: CompiledModel | Path, check: bool = False): RunResult
  }

  class RunResult {
    +returncode: int
    +command: List[str]
    +cwd: Path
    +stdout_path: Path
    +stderr_path: Path
    +is_success: bool
  }
}

Layer "1" *-- "1" Synapses : contains
Layer "1" *-- "*" NeuronOverrideRange : contains
Layer "1" *-- "*" NeuronOverride : contains
NemoSimRunner ..> RunResult : returns
NemoSimRunner ..> CompiledModel : uses

@enduml
```

### Create Sequence Diagram (`docs/diagrams/sequence_diagram.puml`)
```plantuml
@startuml NemoSDK_Sequence_Compile_Run

actor User
participant "Examples/CLI" as CLI
participant "BIUNetworkDefaults" as Defaults
participant "Layer, Synapses" as Model
participant "compile()" as Compiler
participant "CompiledModel" as Compiled
participant "NemoSimRunner" as Runner
participant "NEMOSIM Binary" as Sim

User -> CLI: Create network model
CLI -> Defaults: BIUNetworkDefaults(...)
CLI -> Model: Layer(size, Synapses(...))

CLI -> Compiler: compile(defaults, layers, ...)
Compiler -> Compiler: Validate defaults
Compiler -> Compiler: Validate layers
Compiler -> Compiler: Generate XML
Compiler -> Compiler: Write artifacts
Compiler -> Compiled: CompiledModel(config_path)
Compiler --> CLI: return CompiledModel

CLI -> Runner: NemoSimRunner(working_dir)
CLI -> Runner: runner.run(compiled_model, check=True)
Runner -> Runner: Prepare config.json path
Runner -> Runner: Setup log paths
Runner -> Sim: Execute NEMOSIM binary
Sim --> Runner: Process result
Runner -> Runner: Create RunResult
Runner --> CLI: return RunResult

CLI --> User: Display results

@enduml
```

## Method 3: Using Mermaid - Markdown-Compatible Diagrams

Mermaid diagrams can be embedded in Markdown files and rendered by many tools.

### Create Class Diagram (`docs/diagrams/class_diagram.md`)
```mermaid
classDiagram
    class BIUNetworkDefaults {
        +Optional[float] VTh
        +Optional[float] RLeak
        +Optional[int] refractory
        +Optional[float] VDD
        +Optional[float] Cn
        +Optional[float] Cu
        +Optional[float] fclk
        +Optional[int] DSBitWidth
        +Optional[float] DSClockMHz
        +Optional[str] DSMode
        +validate() None
    }

    class Synapses {
        +int rows
        +int cols
        +List[List[float]] weights
        +validate() None
    }

    class NeuronOverrideRange {
        +int start
        +int end
        +Optional[float] VTh
        +Optional[float] RLeak
        +Optional[int] refractory
        +validate(layer_size) None
    }

    class NeuronOverride {
        +int index
        +Optional[float] VTh
        +Optional[float] RLeak
        +Optional[int] refractory
        +validate(layer_size) None
    }

    class Layer {
        +int size
        +Synapses synapses
        +List[NeuronOverrideRange] ranges
        +List[NeuronOverride] neurons
        +validate() None
    }

    class CompiledModel {
        -Path config_path
        +get_config_path() Path
    }

    class NemoSimRunner {
        -Path working_dir
        -Path binary_path
        +run(config, check) RunResult
    }

    class RunResult {
        +int returncode
        +List[str] command
        +Path cwd
        +Path stdout_path
        +Path stderr_path
        +bool is_success
    }

    Layer "1" *-- "1" Synapses
    Layer "1" *-- "*" NeuronOverrideRange
    Layer "1" *-- "*" NeuronOverride
    NemoSimRunner --> RunResult : returns
    NemoSimRunner --> CompiledModel : uses
```

### Create Sequence Diagram (`docs/diagrams/sequence_diagram.md`)
```mermaid
sequenceDiagram
    participant User
    participant CLI as Examples/CLI
    participant Defaults as BIUNetworkDefaults
    participant Model as Layer, Synapses
    participant Compiler as compile()
    participant Compiled as CompiledModel
    participant Runner as NemoSimRunner
    participant Sim as NEMOSIM Binary

    User->>CLI: Create network model
    CLI->>Defaults: BIUNetworkDefaults(...)
    CLI->>Model: Layer(size, Synapses(...))
    
    CLI->>Compiler: compile(defaults, layers, ...)
    Compiler->>Compiler: Validate defaults
    Compiler->>Compiler: Validate layers
    Compiler->>Compiler: Generate XML
    Compiler->>Compiler: Write artifacts
    Compiler->>Compiled: CompiledModel(config_path)
    Compiler-->>CLI: return CompiledModel

    CLI->>Runner: NemoSimRunner(working_dir)
    CLI->>Runner: runner.run(compiled_model, check=True)
    Runner->>Runner: Prepare config.json path
    Runner->>Runner: Setup log paths
    Runner->>Sim: Execute NEMOSIM binary
    Sim-->>Runner: Process result
    Runner->>Runner: Create RunResult
    Runner-->>CLI: return RunResult

    CLI-->>User: Display results
```

## Method 4: Using Graphviz - Programmatic Diagrams

Install Graphviz and use the DOT language directly or through Python.

### Installation
```bash
# System package
sudo apt-get install graphviz  # Debian/Ubuntu
brew install graphviz          # macOS

# Python wrapper
pip install graphviz
```

### Python Script Example
See `scripts/generate_diagrams.py` (if created) for automated generation.

## Method 5: Online Tools

- **draw.io** (diagrams.net): Free, browser-based, supports UML
- **Lucidchart**: Commercial, professional UML tools
- **Visual Paradigm**: Commercial, comprehensive UML support
- **PlantUML Online**: http://www.plantuml.com/plantuml/uml/

## Recommended Workflow

1. **For quick automated diagrams**: Use `pyreverse`
2. **For version-controlled, text-based diagrams**: Use PlantUML
3. **For documentation in Markdown**: Use Mermaid
4. **For custom/professional diagrams**: Use draw.io or PlantUML

## Next Steps

1. Install your preferred tool
2. Run the generation commands
3. Review and refine the diagrams
4. Add diagrams to your documentation
