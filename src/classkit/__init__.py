"""classkit — tooling for the class-framework.

Three commands matter:

    classkit validate    check a course against its methodology and schemas
    classkit scaffold    create content skeletons from framework templates
    classkit write       write a file, refusing to overwrite existing content

All three run inside a *course* repo. The framework repo itself contains no course
content (D-015), so `validate` has nothing to do here.

`write` is how every agent and command puts content on disk: the refusal to destroy a
teacher's authored work is enforced there, in code, not by prompt (D-031b).
"""

__version__ = "0.1.0"
