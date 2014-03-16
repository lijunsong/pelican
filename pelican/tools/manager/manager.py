from flask import Flask
from flask import render_template


app = Flask(__name__)
app.debug = True

def nest_dir_list(directory):
    dirs = []
    files = []
    for root, ds, fs in os.walk(directory):
        dirs.append(root)
        for f in fs:
            files.append(os.path.join(root, f))
    return (dirs, files)

@app.route('/')
def list_all_categories():
    dirs, files = nest_dir_list("notes")
    return render_template("list_categories.html", dirs)

def main():
    app.run()

if __name__ == '__main__':
    app.run()
