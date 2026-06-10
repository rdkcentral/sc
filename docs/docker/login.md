# sc docker login

`sc docker login` adds a remote container registry to your SC config so
you can `sc docker run <image>` images you don't already have pulled
locally. (For images already pulled, the `--local` flag on `sc docker run`
skips the login flow entirely.)

You'll be prompted for four pieces of input.

## 1. Registry URL

Must include both the **host** and the **namespace** (path), separated by `/`.

| Registry type | Example URL                              |
| ------------- | ---------------------------------------- |
| GHCR          | `ghcr.io/myorg`                          |
| Artifactory   | `your.artifactory.com/docker-registry`   |

> [!IMPORTANT]
> Don't paste the prompt prefix (`> : `) into the answer — paste only the
> URL. Whitespace and leading prompt prefixes are stripped + validated,
> and `sc` will reject the input with a clear error if the URL doesn't
> match the expected `host/namespace` shape (see [#64](https://github.com/rdkcentral/sc/issues/64)).

## 2. Registry Type

Currently the supported registry types are `github` or `artifactory`.

## 3. Use netrc?

- `y` — `sc` reads the username and API key for the registry's host from
  your `~/.netrc` file.
- `n` — `sc` prompts you to enter the username and API key manually, and
  stores them in `~/.sc_config/config.yaml`.

## 4. Username / API Key (only asked if you chose `n`)

| Registry    | Username           | Credential                                                                                                |
| ----------- | ------------------ | --------------------------------------------------------------------------------------------------------- |
| GHCR        | GitHub username    | [Personal Access Token (classic)](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic) |
| Artifactory | Artifactory username | API Key (Profile → API Key) — see note about PAT migration below                                        |

---

## Obtaining Credentials

### GitHub Container Registry (GHCR)

To create a Personal Access Token (PAT) for GitHub, follow the instructions
[here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic).

### Artifactory

Currently, we use API Keys to access Artifactory. Find yours by:

1. Click your profile icon in the top-right corner.
2. Select **Edit Profile**.
3. Scroll down to **API Key**.

> [!NOTE]
> Artifactory will transition to using Personal Access Tokens in Q4 2024.
> We will update this guide with the new instructions at that time.

## Example `.netrc` file

```
machine example.artifactory.com
login <Your Username>
password <Your API Key>

machine ghcr.io
login  <Your Username>
password <Your Personal Access Token>
```

Make sure the file is owned by you and not world-readable:

```shell
chmod 600 ~/.netrc
```

## Troubleshooting

### `not enough values to unpack (expected 2, got 1)` or `No authenticators found for machine '> : …'`

You likely pasted with the prompt prefix included (e.g. `> : ghcr.io/myorg`)
or omitted the namespace. Re-run `sc docker login` and paste the URL only
— `<host>/<namespace>`, no prefix, no trailing slash. Fixed by validation
added in [#64](https://github.com/rdkcentral/sc/issues/64).

### "WARNING: You have not logged into any registries…"

If you only need to run an image you already have pulled, skip login:

```shell
sc docker run <image> --local /bin/bash
```

### Token rejected with `Bad Credentials`

The token in `~/.netrc` or `~/.sc_config/config.yaml` has expired. Generate
a fresh one (see [Obtaining Credentials](#obtaining-credentials)), update
the file, then re-run `sc docker login`.

### Anonymous list works but login fails

Some Artifactory namespaces allow anonymous read. If you only need
`sc docker list` (not `run` of remote images), you can skip login
altogether — leave `~/.sc_config/config.yaml` empty.
