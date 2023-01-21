# hiddifypanel Flask Application

 hiddifypanel to create multi proxy using xray mtproxy and others

# under development do not use it yet
## Installation

From source:

```bash
git clone https://github.com/hiddify/HiddifyPanel hiddifypanel
cd hiddifypanel
make install
```

From pypi:

```bash
pip install hiddifypanel
```

## Executing

This application has a CLI interface that extends the Flask CLI.

Just run:

```bash
$ hiddifypanel
```

or

```bash
$ python -m hiddifypanel
```

To see the help message and usage instructions.

## First run

```bash
hiddifypanel create-db   # run once
hiddifypanel populate-db  # run once (optional)
hiddifypanel add-user -u admin -p 1234  # ads a user
hiddifypanel run
```

Go to:

- Website: http://localhost:5000
- Admin: http://localhost:5000/admin/
  - user: admin, senha: 1234
- API GET:
  - http://localhost:5000/api/v1/product/
  - http://localhost:5000/api/v1/product/1
  - http://localhost:5000/api/v1/product/2
  - http://localhost:5000/api/v1/product/3


> **Note**: You can also use `flask run` to run the application.
