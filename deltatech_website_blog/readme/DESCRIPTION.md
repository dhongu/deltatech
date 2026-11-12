A blog is usually read from the newest post to the oldest, by the date each post was published. This module sets that as the default sort order of blog posts.

- **Publication date**: Blog posts are sorted by their publication date (`published_date`), newest first.
- **Same date**: Posts with the same publication date are sorted by record ID, highest first, so the most recently created post comes first.
- **Default order only**: The order is set on the blog post model itself, so it applies wherever posts are read without a requested order. A screen, filter or query that asks for its own order keeps it.

The module depends on `website_blog`. It adds no field, view, menu, setting or access right, and it does not change the posts themselves.
