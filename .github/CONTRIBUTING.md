# Contributing

## Getting started

- Fork the repository on GitHub.
- Install the development environment. Follow the instructions in the [README](https://github.com/Cadasta/cadasta-platform/blob/master/README.rst#install-for-development).
- Review our [Contributing Style Guide](https://github.com/Cadasta/cadasta-platform/wiki/Contributing-Style-Guide), [Git Workflow](https://github.com/Cadasta/cadasta-platform/wiki/Git-Workflow), and [Code Layout](https://github.com/Cadasta/cadasta-platform/wiki/Code-layout) documentation. Additional information can be found in our [wiki](https://github.com/Cadasta/cadasta-platform/wiki).
- Review our [Decision Records repository](https://github.com/Cadasta/decision-records) for insight into the approved strategic and architectural plans for the Cadasta Platform.

## Making Changes

- From the `master` branch, create a new branch that will contain all of your work. 
- Give your topic branch a meaningful name. For example, if you're working on a bug fix for issue #123, you could call your branch `bugfix/#123`.
- Add tests. Whether you fix a bug or add a new feature, you must add tests to verify your code is working as expected. 

## Submitting your Pull Request

- Make sure all tests pass. You can run the tests locally using `./runtests.py` in the `/vagrant/` directory. 
- Make sure your changes pass checks for coding style. You run the checks locally using `./runtests.py --lint` in the `/vagrant/` directory.
- Give your pull request a meaningful title. The pull request title will end up as the commit message in the commit history. For a bug fix a pull request title could read "Fixes #123 -- Make sure usernames are not case-sensitive". 
- If this is a bug fix, link the issue you are addressing in the PR description. GitHub makes this easy when you type `#123` (123 is the number of the issue) the text is automatically linked. 
- When you open a new pull request, you will find four questions that help you to provide us the information we need to review your PR. You should respond to the first question (_Proposed changes in this pull request_) sufficiently. Please describe the changes you have made and why you had to make those changes. If your PR fixes a bug, please include a description of the cause of the bug as well. 
- You do not need to worry about the checklist in the pull request template. The list helps us to remember important things to look at when reviewing. You can use the list, however, as a guideline to prepare your pull request. 

After you submit your pull request, two members of the Cadasta development team will review your changes. 

