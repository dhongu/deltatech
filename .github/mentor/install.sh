# What test.yml installs besides test-requirements.txt, for Mentor's screenshots job
# (sourced by terrabit-solutions/ci-agents, after the private clones, without credentials).
# Keep in step with test.yml.
pip install "requests>=2.27.0"
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
