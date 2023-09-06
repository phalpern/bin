#! /usr/bin/perl -w

use strict;
use English;

my @options;
$" = " ";

my @iosfiles;

sub process
{
    my $input = shift @ARG;
    my @dependencies;

    for my $file (@ARG)
    {
        next if $file =~ /depcheck\./;  # Skip synthetic file
        next if $file =~ m(^/);         # Skip absolute path names
        while ($file =~ m(\.\./))
        {
            print $file, "\n";
            $file =~ s([^/]+/\.\./)();
        }

        push @dependencies, $file
    }
    
    print "$input: @dependencies\n";
}

for my $arg (@ARGV)
{
    if ($arg =~ /^-/) {
        push @options, $arg;
    }
    else {
        my $results = `g++ -M @options -DCHECK='\"$arg\"' $ENV{HOME}/bin/depcheck.cpp`;
        my @depfiles = split(/[ \\\n\t]+/, $results);
        process $arg, @depfiles
    }

}
