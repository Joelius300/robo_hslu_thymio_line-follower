# ROBO HSLU Thymio line follower

## Setup

1. Update the submodule with `git submodule update`.
2. Create virtual environment for this project ("robo_thymio" or update .python-version)
3. Install requirements from requirements.txt
4. Use that venv as environment/interpreter for this project and the thymio library submodule when needed

You can also do it without virtual environment, especially if you only ever use the thymiodirect library from source and
don't install it.

### Use thymiodirect directly from submodule (recommended)

Import tyhmiodirect via `thymio_python.thymiodirect` instead of `thymiodirect`

Note that you can do this and get the benefits of it even if you have thymiodirect installed as package.
Still I would recommend uninstalling the package with `pip uninstall thymiodirect` to avoid version mismatch-bugs.

### Install thymiodirect as package

See README inside thymio_python directory. If you do this, you will need to reinstall the library everytime it
something changes aka the submodule is updated.

### Working with submodule over ssh instead of http (optional)

```bash
git config url."ssh://git@".insteadOf https://
```
