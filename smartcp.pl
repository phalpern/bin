#!/usr/bin/perl -w

use strict;
use English;
use Getopt::Std;
use File::Basename;
use File::Spec;
use Cwd 'abs_path';

sub usage
{
    die "$ARG[0]\nUsage: smartcp <file> ... [ <destfile> | <destdir> ]\n";
    exit 2;
}

my @originalArgv = @ARGV;

my %options;

# Recognize all 'cp' options.
getopts("fiprR", \%options);

usage "Not enough file arguments" if (@ARGV < 2);

if ($options{'i'} || $options{'r'} || $options{'R'})
{
    exec("cp", @originalArgv) or die "Unable to exec 'cp' command\n";
}

my $target = pop @ARGV;
my $targetdir;

if (-d $target)
{
    $targetdir=abs_path($target);
}
else
{
    $targetdir=abs_path(dirname($target));
}

while (@ARGV)
{
    my $source = shift @ARGV;
# print "smartcp: copying $source\n";

    my ($base,$dir,$ext) = fileparse($source, qr(\.[^.]+));

    if (($ext eq ".cpp" || "$ext" eq ".h") && $targetdir =~ m(unix-) )
    {
        if (-d $target)
        {
            $target = File::Spec->catfile("$target", "$base$ext");
        }

# print "smartcp: Special target: $target\n";
        unlink("$target");

#         system("ln", "-s", File::Spec->catfile(abs_path($dir), "$base$ext"),
#                $target);

        $source = File::Spec->catfile(abs_path($dir), "$base$ext");
        my $guard = "INCLUDED_" . uc($base);
        $guard =~ s/[^A-Z0-9_]/_/g;

        open TARGET, "> $target" or die "Cannot open $target";
        print TARGET "#include <$source>\n";
        close TARGET;
    }
    else
    {
        my @cpopts = ();
        push @cpopts, "-f" if ($options{'f'});
        push @cpopts, "-p" if ($options{'p'});
# print "smartcp: Running @cpopts $source $target\n";
        system("cp", @cpopts, $source, $target);
    }
}
