#! /usr/bin/perl -w

use strict;
use English;

sub usage
{
    print STDERR "@ARG\n" if (@ARG);
    print STDERR "Usage: usage2code [ infile ]\n";
    exit 2;
}

usage "Only one input file may be specified" if (@ARGV > 1);

if (@ARGV)
{
    close STDIN;
    open(STDIN, '<', "$ARGV[0]") or
        die "usageTocode.pl Cannot open file $ARGV[0]\n";
}

my $line;
my $isCode = 0;
my $exampleNum = 0;
my $extraIndent = undef;
while (defined($line = <STDIN>))
{
    $line =~ s/assert/ASSERT/g;

    if ($line =~ m(^// ?```) or $line =~ m(^//\.\.)) {
        $isCode = ! $isCode;
        $extraIndent = undef;
        print "// ```\n";
        next;
    }

    if ($isCode)
    {
        $line =~ s(^// *$)();  # Empty comment line
        $line =~ s(^//)(  );   # Uncomment start of line

        # If indent length is one less than a multiple of 4 (i.e., the
        # remainder is 3), then add an extra space of indent at the start of
        # the line to bring it to normal indentation.  If $extraIndent is set
        # to true for a code section, then it remains true for the remainder of
        # the section.
        if (! defined($extraIndent) and $line =~ m(^( +)[^ ])) {
            $extraIndent = (length($1) % 4 == 3);
        }

        $line = ' ' . $line if $extraIndent;

        # Comment out '#include' within test driver (it should go at the top)
        $line =~ s(^    #include)(//  #include);

        if ($line =~ m/\bmain\(/ ) {
            ++$exampleNum;
            $line =~ s/\bint +main\(/void usageExample$exampleNum\(/x ;
        }
    }
    print $line;
}
