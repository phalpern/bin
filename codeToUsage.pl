#! /usr/bin/perl -w

use strict;
use English;

sub usage
{
    print STDERR "@ARG\n" if (@ARG);
    print STDERR "Usage: code2usage [ infile ]\n";
    exit 2;
}

usage "Only one input file may be specified" if (@ARGV > 1);

if (@ARGV)
{
    close STDIN;
    open(STDIN, '<', "$ARGV[0]") or
        die "codeToUsage.pl Cannot open file $ARGV[0]\n"
}

my $line;
my $isCode = 0;
my $isFirstCode = 1;
my $indented = 0;
while (defined($line = <STDIN>))
{
    $line =~ s/\bASSERT\b/assert/g;

    if ($line =~ m(^// ?```) or $line =~ m(^//\.\.))
    {
        $isCode = ! $isCode;
        print "// ```\n";
        next;
    }

    if ($isCode) {
        # Lines starting with "//! " are commented out in the test driver but
        # should show up as normal code in the header file; replace by four
        # spaces.
        $line =~ s(^//! )(    );

        # '#include' directives are commented out in the test driver but should
        # show up normally in the header file (not doubly commented).
        $line =~ s(^//  *#include)(    #include);
    }
    else {
        $line = "//\n" if ($line eq "\n");
    }

    # Every code line should be indented by 4 spaces unless such a code
    # line is commented out in the test driver itself, in which case it
    # starts with a comment delimiter followed by at least two spaces.  A
    # line starting with a comment delimiter is expected in descriptive
    # text, not code and a line not starting with a comment delimiter is
    # expected only in code.
    if ($isCode == ($line =~ m(^//)))
    {
        print "// ```\n";
        $isCode = ! $isCode;
    }

    if (not $isCode)
    {
        print $line;
        next;
    }

    if ($isFirstCode)
    {
        $indented = ($line =~ m(^    ));
        $isFirstCode = 0;
    }

    $line =~ s/\b(void|int) +usageExample[0-9]*\(/int main\(/;
    $line =~ s/\b(void|int) +usageCase[0-9]*\(/int main\(/;

    $line =~ s(^    )() if ($indented);
    print "//  $line";
}

print "// ```\n" if ($isCode);
