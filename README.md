# bayz: live coding with Bayesian Program Learning
bayz is a live coding platform that fuses the latest and greatest of Bayesian
machine learning with performative music. For more information about the
platform itself, check out [this post](www.google.com).

## Setting up
First, you will need access to Python >=3.8 (version 3.6 is probably fine, but
untested. Anything lower is guaranteed to not work) along with the corresponding
`pip` package manager. Clone the repo and install the required Python packages
with

```sh
git clone https://github.com/wtong98/bayz.git
cd bayz
pip install -r requirements.txt
```

Then, to train a BPL model, do
```sh
python -m bayz.train
```
which will take a good few minutes to download the corpus, train the models, and
save them to disk. Once that finishes, if you'd like to check that your model
trained successfully, try generating a short snippet of music

```sh
python -m bayz.generate
```
Note: you may need to configure `music21` to use a musicxml reader to view
the generated snippet of music. See [their tutorial](https://web.mit.edu/music21/doc/usersGuide/usersGuide_08_installingMusicXML.html) for details.


Live coding itself happens via a jupyter notebook. If you prefer a jupyter
plugin via your favorite text editor, a preformmated file has been provided for
you in `live.py`. Otherwise, boot up jupyter notebook

```sh
jupyter notebook
```

and navigate to `live.ipynb`. Execute the first cell to start a bayz server
and load up a band.

The final component is bayz beat, the audio client. Navigate to a [publicly hosted client](www.google.com)
or launch your own instance with `www/index.html`. Hit start to begin receiving
from your local bayz server instance.

And now you're all set! Execute the indicated cell in the jupyter notebook
to make your music. Try

```python
b.add_line([60, 63, 67, 70], rhythm=[1,2], instrument='sine')
```
to play custom notes, or

```python
b.add_player(rhythm=[1], instrument='sine')
```
to have the machine come up with notes for you.

Play around with different settings. Probe the documentation (especially in
`bayz/music.py`) for new settings to try. Make it your own, and hope you
enjoy!
