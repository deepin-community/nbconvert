"""
Convert between any two formats using pandoc,
and related filters
"""

import os

from pandocfilters import Image, applyJSONFilters  # type:ignore[import-untyped]

from nbconvert.utils.base import NbConvertBase
from nbconvert.utils.pandoc import pandoc

__all__ = ["ConvertExplicitlyRelativePaths", "convert_pandoc"]


def convert_pandoc(source, from_format, to_format, extra_args=None):
    """Convert between any two formats using pandoc.

    This function will raise an error if pandoc is not installed.
    Any error messages generated by pandoc are printed to stderr.

    Parameters
    ----------
    source : string
        Input string, assumed to be valid in from_format.
    from_format : string
        Pandoc format of source.
    to_format : string
        Pandoc format for output.

    Returns
    -------
    out : string
        Output as returned by pandoc.
    """
    return pandoc(source, from_format, to_format, extra_args=extra_args)


# When converting to pdf, explicitly relative references
# like "./" and "../" doesn't work with TEXINPUTS.
# So we need to convert them to absolute paths.
# See https://github.com/jupyter/nbconvert/issues/1998
class ConvertExplicitlyRelativePaths(NbConvertBase):
    """A converter that handles relative path references."""

    def __init__(self, texinputs=None, **kwargs):
        """Initialize the converter."""
        # texinputs should be the directory of the notebook file
        self.nb_dir = os.path.abspath(texinputs) if texinputs else ""
        self.ancestor_dirs = self.nb_dir.split("/")
        super().__init__(**kwargs)

    def __call__(self, source):
        """Invoke the converter."""
        # If this is not set for some reason, we can't do anything,
        if self.nb_dir:
            return applyJSONFilters([self.action], source)
        return source

    def action(self, key, value, frmt, meta):
        """Perform the action."""
        # Convert explicitly relative paths:
        # ./path -> path  (This should be visible to the latex engine since TEXINPUTS already has .)
        # ../path -> /abs_path
        # assuming all relative references are at the start of a given path
        if key == "Image":
            # Image seems to have this composition, according to https://github.com/jgm/pandoc-types
            attr, caption, [filename, typedef] = value

            if filename[:2] == "./":
                filename = filename[2:]
            elif filename[:3] == "../":
                n_up = 0
                while filename[:3] == "../":
                    n_up += 1
                    filename = filename[3:]
                ancestors = "/".join(self.ancestor_dirs[:-n_up]) + "/"
                filename = ancestors + filename
            return Image(attr, caption, [filename, typedef])
        # If not image, return "no change"
        return None
