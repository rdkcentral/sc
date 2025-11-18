import click
from collections import defaultdict

class GroupedHelp(click.Group):
    def format_commands(self, ctx, formatter):
        sections = defaultdict(list)
        for name in self.list_commands(ctx):
            cmd = self.get_command(ctx, name)
            if cmd is None:
                continue
            if cmd.hidden:
                continue

            sec = getattr(cmd, "section", None)
            sections[sec].append((name, cmd.get_short_help_str()))
        
        for sec, rows in sections.items():
            title = f"{sec} Commands" if sec else "Other Commands"
            # formatter.write_heading(title)

            with formatter.section(title):
                formatter.write_dl(rows)