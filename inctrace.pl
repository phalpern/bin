#! /usr/bin/perl -w
#
# Filter for output of "CC -E" or "g++ -E" which produces tree of #include
# nesting.

use strict;
use English;

my @filestack = ();
my %linemap;
my $spaces = "                                                            ";

my $line;
my $currfile = "";
while (defined($line = <STDIN>))
{
    next unless ($line =~ m{\# *([0-9]+)[ :]*"(.*)"}o );

    my $linenum = $1;
    my $filename = $2;
    $filename =~ s(/include/unix-*/dbg_exc_mt/)(/);
    $filename =~ s(^/bbcm/packages.git/groups/bde/)();

    if ($filename eq $currfile)
    {
        $linemap{$filename}->[0] = $linenum;
        next;
    }
    
    if (exists($linemap{$filename}))
    {
        if ($linemap{$filename} < $linenum)
        {
            while ($filestack[$#filestack] ne $filename)
            {
                # Must be popping back to previous level
                shift @$linemap{pop @filestack};
            }
        }
        else
        {
            push @filestack, $filename;
            printInclude @filename;
        }

        unshift @$linemap{$filename}, $linenum;
        $currfile = $filename;
    }
    else
    {
        push @filestack, $filename;
        $linemap{$filename} = [ $linenum ];
        printInclude @filename;

        $currfile = $filename;
    }
    
}
