# Copyright 2025 RDK Management
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import click
from collections import defaultdict

class GroupedHelp(click.Group):
    """
    This class allows to set 'section' and 'section_order' attributes on click commands.

    Then in the help message commands will be organised by section, in the section order
    provided.
    """
    def format_commands(self, ctx, formatter):
        sections = defaultdict(list)
        section_order = {}

        for name in self.list_commands(ctx):
            cmd = self.get_command(ctx, name)
            if cmd is None:
                continue
            if cmd.hidden:
                continue

            sec = getattr(cmd, "section", None)
            order = getattr(cmd, "section_order", 50)

            sections[sec].append((name, cmd.get_short_help_str()))
            section_order[sec] = order

        for sec in sorted(sections, key=lambda s: section_order.get(s, 50)):
            rows = sections[sec]
            title = f"{sec} Commands" if sec else "Other Commands"

            with formatter.section(title):
                formatter.write_dl(rows)
