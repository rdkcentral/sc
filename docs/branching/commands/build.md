# Branching Build Command

Runs build commands defined in a YAML config, used to simplify running builds for developers.

## Usage

`sc build <arguments> <defined> <by> <config>`

## Config Example

```yaml
commands:
  list:
    description: Run each command listed in the command.
    # As the command is a list, each command here will be run individually, in sequence.
    command:
      - echo "echo 1"
      - echo "echo 2"
      - echo "echo 3"
      - echo "echo 4"
  list_passthrough:
    description: Run each command listed, substituting the extra args in.
    # As above, since passthrough is set to True all $@ will be replaced with all arguments
    # following list_passthrough
    command:
      - echo "echo 1"
      - echo "$@"
      - echo "echo 2"
      - echo "$@"
    params:
      passthrough: true
  command_with_args:
    description: This command takes postional arguments.
    command: echo {{greeting}} {{name}}
    args:
      greeting:
        description: This description for the arg shows in the help message.
      name:
        description: Must choose one of the names provided in choices.
        choices:
          - Jane
          - Sam
          - Lisa
```

In the above example the build commands you run include:
`sc build list` - Which would run the 4 echo commands in order.
`sc build list_passthrough <argument>` - Run the 4 echo commands with the argument substituted for the "$@"s.
`sc build command_with_args Hello Lisa` - Would echo "Hello Lisa" and error if the second argument isn't one of the provided choices.
