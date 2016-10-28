from fabric.api import *
import os,sys
 
project_dir = os.path.join(os.path.dirname(sys.argv[0]))
def first_setup():

    # 1. Make a new virtualenv
    local("mkvirtualenv photokeeper")

    # pip install packages
    with prefix('workon photokeeper'):
        local("pip install pytest")

def build_windows_dist():
    if os.name == 'nt':
        # Call the pyinstaller
        local("python ../pyinstaller/pyinstaller.py photokeeper_windows.spec --onefile")


def run_tests():
    test_dir = "test"
    with lcd(test_dir):
        # Regenerate the test script
        local("py.test --genscript=runtests.py")
        t = local("py.test --cov-config .coveragerc --cov=photokeeper --cov-report=term --cov-report=html", capture=False)



def push_docs():
    """ Build the sphinx docs from develop
        And push it to gh-pages
    """
    githubpages = "/Users/virantha/dev/githubdocs/photokeeper"
    # Convert markdown readme to rst
    #local("pandoc README.md -f markdown -t rst -o README.rst")
    with lcd(githubpages):
        local("git checkout gh-pages")
        local("git pull origin gh-pages")
    local("head CHANGES.rst > CHANGES_RECENT.rst")
    local("tail -n 1 CHANGES.rst >> CHANGES_RECENT.rst")
    with lcd("docs"):
        print("Running sphinx in docs/ and building to ~/dev/githubpages/photokeeper")
        local("make clean")
        local("make html")
        local("cp -R ../test/htmlcov %s/html/testing" % githubpages)
    with lcd(githubpages):
        local("git add .")
        local('git commit -am "doc update"')
        local('git push origin gh-pages')
