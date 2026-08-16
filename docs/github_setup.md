# Private GitHub setup

Create an empty **private** repository named `insured-but-unprotected`. Do not
initialize it with another README or license because both are included here.

From the extracted project directory:

```bash
git init
git add .
git commit -m "Initialize CMS Marketplace data feasibility audit"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/insured-but-unprotected.git
git push -u origin main
```

Then open the repository's **Settings > Collaborators** page and invite the
intended collaborator by GitHub username.

## Before making the repository public

- Verify every state-law observation twice.
- Add the missing CMS dictionaries and historical files.
- Decide whether public source files should remain committed or be distributed
  through a release because of repository size.
- Confirm authorship and citation metadata.
- Never commit licensed IQVIA data or credentials.
