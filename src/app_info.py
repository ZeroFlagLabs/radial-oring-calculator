"""Central application identity and public GitHub repository information.

The repository is public. A stable release is not assumed to exist until
the corresponding release is actually published on GitHub.
"""

APP_TITLE = 'Static & Dynamic Radial O-Ring Calculator'
APP_VERSION = '1.0.0'
GITHUB_REPOSITORY = 'ZeroFlagLabs/radial-oring-calculator'
GITHUB_URL = 'https://github.com/' + GITHUB_REPOSITORY
RELEASES_URL = GITHUB_URL + '/releases/latest'
RELEASE_API_URL = 'https://api.github.com/repos/' + GITHUB_REPOSITORY + '/releases/latest'
