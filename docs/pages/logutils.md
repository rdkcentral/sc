# SC Logger Manager Guide

The SC Logger Manager provides a unified way for plugins to utilise logging.

Currently it provides a way for plugins to register the loggers it wants to send to stdout but in the future it can perform things such as having a centralised logging file for SC or for each plugin separately etc.

To use the logger manager import it to the cli.py of your plugin<sup>1</sup> and then initialise it with the name of your plugin 

`log_manager = SCLoggerManager("sc-clone")`

Then register which loggers you want, the obvious one being your plugin:

`log_manager.add_logger(["sc_clone"])`

The reason for this is as parts split into separate repos for reusibility we can make sure they still follow the same logging rules by registering them with the manager:

`log_manager.add_logger(["sc_clone", "my_sc_repo"])`

It also means that the logging messages use the name of the plugin you created the manager with rather than the name of the logger itself which may be unhelpful, but running in debug mode provides you with both for extra information.

Example of an info message for sc-clone:

`[INFO] [sc-clone] Hello world!`

Example with debug mode:

`[INFO] [sc-clone] sc_clone.module1.module2 : Hello World!`

<sup>1</sup> Or in the future it will come with the plugin base class.