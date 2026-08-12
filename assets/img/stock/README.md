Self-hosted copies of the Unsplash photos this site links to, one file per
(photo id, width) pair actually used -- so each page still gets the same size
it asked for, just from this repo instead of images.unsplash.com.

Filename scheme: {unsplash-photo-id}-w{width}.jpg

photo-1577962917302-cd874c4e31d2-w2000.jpg came from a page that linked the
Unsplash "/flagged/" variant of this photo, which now 404s upstream (the
image was pulled or re-flagged on Unsplash's end, unrelated to anything on
our side) -- fetched from the normal path instead, same photo.
