# =============================================================================
#  latexmk configuration for both theses.
#
#     latexmk main_master.tex        # -> build/master/main_master.pdf
#     latexmk main_ingenieur.tex     # -> build/ingenieur/main_ingenieur.pdf
#     latexmk -c main_master.tex     # remove intermediates, keep the PDF
#     latexmk -C main_master.tex     # remove everything including the PDF
#
#  Name one thesis per run. Each has its own folder, so cleaning or rebuilding
#  one never touches the other's files.
#
#  Every intermediate file lands under build/ instead of beside the sources. They
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

# -- one output folder per thesis: build/master/, build/ingenieur/ -------------
# latexmk has no per-file $out_dir, but it reads this file before it parses its
# arguments, so the folder is taken from the thesis named on the command line.
# An explicit -outdir=... on the command line still wins. build/ is covered by
# the repo .gitignore.
{
    my @mains = grep { /^main_(\w+)(?:\.tex)?$/ } @ARGV;
    my $info  = grep { /^--?(?:v|version|h|help|commands|showextraoptions)$/ } @ARGV;
    if (@mains == 1) {
        my ($doc) = $mains[0] =~ /^main_(\w+)/;
        $out_dir = "build/$doc";
    } elsif (!$info) {
        die "latexmk: name exactly one thesis, e.g. `latexmk main_master.tex` or "
          . "`latexmk -C main_ingenieur.tex`; each builds into its own build/<thesis>/ folder.\n";
    }
}

# -- glossaries: latexmk does not know about makeglossaries on its own --------
add_cus_dep('acn', 'acr', 0, 'makeglossaries');
add_cus_dep('glo', 'gls', 0, 'makeglossaries');
sub makeglossaries {
    my ($base_name, $path) = fileparse($_[0]);
    return system('makeglossaries', '-d', $path, $base_name);
}

# -- so `latexmk -c` also clears the glossaries and biber leftovers -----------
$clean_ext .= ' acn acr alg glg glo gls glsdefs ist run.xml bbl synctex.gz';
