# =============================================================================
#  latexmk configuration for both theses.
#
#     latexmk main_master.tex        # or main_ingenieur.tex
#     latexmk -c                     # remove intermediates, keep the PDF
#     latexmk -C                     # remove everything including the PDF
#
#  Every intermediate file lands in build/ instead of beside the sources. They
#  are NOT optional -- .aux carries cross-references between passes, .toc/.lof/
#  .lot carry the contents lists, .bcf feeds biber, .bbl is what biber hands
#  back to be typeset, .acn/.acr/.glo/.gls drive the acronym list, .out holds
#  the PDF bookmarks, and .log is the only record of what went wrong. Deleting
#  them mid-build gives you a document full of "??". Keeping them out of the
#  source directory is the part that is actually worth doing.
# =============================================================================

$pdf_mode = 5;          # 5 = XeLaTeX. Required: polyglossia + Arabic.
$xelatex  = 'xelatex -interaction=nonstopmode -file-line-error -synctex=1 %O %S';

$bibtex_use = 2;        # run biber, and let `latexmk -c` clear the .bbl too
$out_dir = 'build';     # already covered by the repo .gitignore

# -- glossaries: latexmk does not know about makeglossaries on its own --------
add_cus_dep('acn', 'acr', 0, 'makeglossaries');
add_cus_dep('glo', 'gls', 0, 'makeglossaries');
sub makeglossaries {
    my ($base_name, $path) = fileparse($_[0]);
    return system('makeglossaries', '-d', $path, $base_name);
}

# -- so `latexmk -c` also clears the glossaries and biber leftovers -----------
$clean_ext .= ' acn acr alg glg glo gls glsdefs ist run.xml bbl synctex.gz';
