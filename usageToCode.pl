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
while (defined($line = <STDIN>))
{
    $line =~ s/assert/ASSERT/g;

    if ($line =~ m(^//\.\.))
    {
        $isCode = ! $isCode;
        print $line;
        next;
    }

    if ($isCode)
    {
        $line =~ s(^//)(  );

        # Comment out '#include' within test driver (it should go at the top)
        $line =~ s(^    #include)(//  #include);

        if ($line =~ m/\bmain\(/ )
        {
            ++$exampleNum;
            $line =~ s/\bint +main\(/void usageExample$exampleNum\(/x ;
        }
    }
    print $line
}
