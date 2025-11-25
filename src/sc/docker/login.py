from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, HSplit
from prompt_toolkit.widgets import TextArea, Button, Label, Box
from prompt_toolkit.shortcuts import choice, input_dialog

def tui():
    result = choice(
        message="Select the registry your images are stored in from the buttons below:",
        options=[
            ("github", "Github"),
            ("artifactory", "Artifactory")
        ],
        default="github"
    )
    registry_url = input_dialog(
        title="Registry URL",
        text="Enter the registry URL e.g. your.artifactory.com/docker-registry"
    ).run()

    print(result)
    print(registry_url)

def form():
    name = TextArea(height=1)
    email = TextArea(height=1)
    result = {}

    def accept():
        result["name"] = name.text
        result["email"] = email.text
        app.exit(result=result)

    def cancel():
        app.exit(result=None)

    root = HSplit([
        Label("Enter details:"),
        Label("Name:"), name,
        Label("Email:"), email,
        HSplit([
            Button(text="OK", handler=accept),
            Button(text="Cancel", handler=cancel),
        ])
    ])

    app = Application(
        layout=Layout(root, focused_element=name),
        full_screen=False,
    )
    return app.run()

if __name__ == "__main__":
    tui()