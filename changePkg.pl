#! /usr/bin/perl -w
#
# Rename a component, optionally changing it to namespace format.

use strict;
use English "-no_match_vars";

use FileHandle;
use File::Basename;
use File::Spec::Functions;
use File::Path;

sub usage(;$)
{
    my $message = $_[0];
    print STDERR $message, "\n" if ($message);
    print STDERR
      "Usage: changePkg.pl [<options>] <srcfile> <dstfile> OR\n",
      "       changePkg.pl [--newstyle] [-v] <srcfile>... <dstdir> OR\n",
      "       changePkg.pl [--newstyle] [-v] <srcdir>... <dstdir> OR\n",
      "   Options:\n",
      "       --verbose | -v: Verbose output\n",
      "       --nsstyle     : New package(s) use package namespaces\n",
      "       --prefixstyle : New package(s) use package prefixes (default)\n",
      "       --export=file : Export package mapping to file\n",
      "       --import=file : Import package mapping from file (can repeat)\n";
        
    exit(-2);
}

my %pkgmap;
my %filemap;

sub importFromFile($)
{
    my $mapFileName = $_[0];
    my $mapFile = new FileHandle("< $mapFileName");
    die "Unable to open map file: $mapFileName for reading." unless $mapFile;
    while (defined(my $line = <$mapFile>)) {
        my ($oldpkg, $newpkg, $nsstyle) = split /\s/, $line;
        die "Invalid line: $line in $mapFileName" unless $newpkg;
        $pkgmap{$oldpkg} = [ $newpkg, $nsstyle ];
    }
    $mapFile->close;
}

sub exportToFile($)
{
    my $mapFileName = $_[0];
    my $mapFile = new FileHandle("> $mapFileName");
    die "Unable to open map file: $mapFileName for writing." unless $mapFile;
    while (my ($srcpkg, $dstpkg) = each %pkgmap) {
        print $mapFile $srcpkg, " ", $dstpkg->[0], " ", $dstpkg->[1], "\n";
    }
    $mapFile->close;
}

# The number of open braces minus the number of close braces in the specified
# line.  The line is assumed to have already been stripped of comments.
# The return value might be negative.
sub countBraces($)
{
    my $openBraces  = $_[0];
    my $closeBraces = $_[0];
    $openBraces  =~ s/[^\{]+//g;  # Remove all except open braces
    $closeBraces =~ s/[^\}]+//g;  # Remove all except close braces

    return length($openBraces) - length($closeBraces);
}

my $nsstyle = 0;
my $verbose = 0;
my $exportfile;
my @fileargs;
for my $opt (@ARGV) {
    usage if $opt eq "--help" || $opt eq "-h";
    if ($opt eq "--nsstyle") { $nsstyle = 1;  next; }
    if ($opt eq "--prefixstyle") { $nsstyle = 0;  next; }
    if ($opt eq "--verbose" || $opt eq "-v") { $verbose = 1; next; } 
    if ($opt =~ /^--export=(.*)/) { $exportfile = $1; next; }
    if ($opt =~ /^--import=(.*)/) { importFromFile($1); next; }
    usage("Invalid argument: ".$opt) if $opt =~ /^-/;
    push @fileargs, $opt;
}

sub verbose(@) {
    print STDERR "@_\n" if ($verbose);
}

usage("Too few file/directory arguments") if @fileargs < 2;

my $dst = pop @fileargs;
my $dstbase = basename($dst);
my $dstdir = $dst;
$dstdir = dirname($dstdir) if (-f $dstdir);
usage("No such directory $dstdir") unless (-d $dstdir);

$dstbase =~ m/^([a-z][a-z0-9_][a-z0-9]+)/;
my $dstPkgOrGrp = $1;
verbose("dstPkgOrGrp = $dstPkgOrGrp,", "dstdir = $dstdir");
my $isGroup = ($dstPkgOrGrp =~ /^[a-z][a-z0-9][a-z0-9]$/);

if (1 == @fileargs && -f $fileargs[0]) {
    # Map single src file and package names to dst file and package names

    if ($isGroup) {
        usage("Dstination must not be a group if only one source file");
    }

    my $srcfilename = $fileargs[0];
    my $srcbasename = basename($srcfilename);
    $srcbasename =~ m/(^[a-z][a-z0-9_][a-z0-9]+)/;
    my $srcpackage = $1;

    my $dstfilename;
    if (-d $dst) {
        # Construct dst file name by replacing package prefix in src file
        # name with the dst package name, then appending it to the dstination
        # directory.
        my $dstbasename = $srcbasename;
        $dstbasename =~ s/^${srcpackage}_/${dstPkgOrGrp}_/x;
        $dstfilename = catfile($dstdir, $dstbasename);
    }
    else {
        $dstfilename = $dst;
    }

    $pkgmap{$srcpackage} = [ $dstPkgOrGrp, $nsstyle ]
        unless ($srcpackage eq $dstPkgOrGrp);
    $filemap{$srcfilename} = $dstfilename;

    verbose "srcpackage = $srcpackage, dstPkgOrGrp = $dstPkgOrGrp";
    verbose "srcfilename = $srcfilename, dstfilename = $dstfilename";

    pop @fileargs;
}
elsif (-f $dst) {
    usage("Dstination must be a directory if more than one source");
}

# Expand any source directories into their constituent files
my @srcfiles;
for my $filearg (@fileargs) {
    if (-f $filearg) {
        push @srcfiles, $filearg;
    }
    else {
        my $pkg = basename($filearg);
        for my $dir ($filearg,
                     catfile($filearg, "package"),
                     catfile($filearg, "doc")) {
            opendir SRCDIR, $dir or die "Cannot read directory $filearg";
            while (defined(my $filename = readdir SRCDIR)) {
                my $filepath = catfile($dir, $filename);
                if ($filename =~ /^$pkg/x && -f $filepath) {
                    push @srcfiles, $filepath;
                }
            }
            closedir SRCDIR;
        }
    }
}

# Map src file and package names to dst file and package names
for my $srcfilename (@srcfiles) {
    my $srcbasename = basename($srcfilename);
    $srcbasename =~ m/(^[a-z][a-z0-9_][a-z0-9]+)/;
    my $srcpackage = $1;
    my $dstpackage;
    if ($isGroup) {
        # Construct the dst package name by replacing the group portion of
        # the src package name.
        $dstpackage = $srcpackage;
        $dstpackage =~ s/^.../$dstPkgOrGrp/x;
    }
    else {
        $dstpackage = $dstPkgOrGrp;
    }
    
    # Construct the dst file name by replacing the package portion of the src
    # file name by the dst package name.
    my $dstbasename = $srcbasename;
    $dstbasename =~ s/^$srcpackage/$dstpackage/x;
    my $dstsubdir = "";
    $dstsubdir = "doc" if basename(dirname($srcfilename)) eq "doc";
    $dstsubdir = "package" if basename(dirname($srcfilename)) eq "package";
    my $dstfilename;
    if ($isGroup) {
        $dstfilename = catfile($dstdir, $dstpackage, $dstsubdir, $dstbasename);
    }
    else {
        $dstfilename = catfile($dstdir, $dstsubdir, $dstbasename);
    }

    $pkgmap{$srcpackage} = [ $dstpackage, $nsstyle ]
        unless ($srcpackage eq $dstPkgOrGrp);
    $filemap{$srcfilename} = $dstfilename;
}

verbose("Package map:");
while (my ($srcpkg, $dstpkg) = each %pkgmap) {
    verbose("    $srcpkg => [ $dstpkg->[0], $dstpkg->[1] ]");
}

verbose("\nFile map:");
while (my ($srcfile, $dstfile) = each %filemap) {
    verbose("    $srcfile => $dstfile");
}

@srcfiles = keys %filemap;
@srcfiles = sort @srcfiles;

for my $srcfilename (@srcfiles) {

    my $dstfilename = $filemap{$srcfilename};

    verbose("Processing $srcfilename into $dstfilename");

    basename($srcfilename) =~ m/^([a-z][a-z0-9_][a-z0-9]+)/;
    my $srcpkg = $1;
    basename($dstfilename) =~ m/^([a-z][a-z0-9_][a-z0-9]+)/;
    my $dstpkg = $1;
    
    my $srcfile = new FileHandle "< $srcfilename";
    die "Cannot open $srcfilename for reading" unless $srcfile;
    
    # Read entire source into memory.  This gives us some random-access.
    my @lines = <$srcfile>;
    my $isCppFile = ($srcfilename =~ /(\.cpp|\.h)$/);
    my $isTstDrvr = ($srcfilename =~ /(\.t\.cpp)$/);
    my $opennamespace;
    my $braceLevel = 0;
#    my $lineidx = -1;
    for my $line (@lines) {
#        ++$lineidx;

        if ($nsstyle && $isCppFile) {
            my $ncline = $line;
            $ncline =~ s(//.*)();  # Remove comment

            # Remember start of BloombergLP namespace so that we can insert
            # start of package namespace (but not within a test driver).
            if ($ncline =~ /namespace\s+BloombergLP\s+\{/ && ! $isTstDrvr) {
                $opennamespace = \$line;
                $braceLevel = 0;
            }
            $opennamespace = undef 
                if ($ncline =~ /namespace\s+$dstpkg\s+\{/); # avoid dup ns

            if (defined($opennamespace)) {
                # Remove package prefix within package namespace
                $line =~ s/\b${srcpkg}_//xg;

                # Search for close namespace
                $braceLevel += countBraces($ncline);
                if ($braceLevel <= 0) {
                    # Insert package namespace into BloombergLP namespace
                    $$opennamespace .= "namespace $dstpkg {\n";
                    $line = "} // close namespace $dstpkg\n" . $line;

                    $opennamespace = undef;
                }
            }
        } # end if nsstyle

        while (my ($oldpkg, $newpkgStruct) = each %pkgmap) {
            # Translate old package prefixes to new package ns qualifiers.
            my $newpkg     = $newpkgStruct->[0];
            my $newNsStyle = $newpkgStruct->[1];

            if ($newNsStyle && $isCppFile) {
#                0 != $lineidx && $line !~ /\#\s*include/)

                # Change class name from old prefix notation to namespace
                # prefix.  This is only for class names (lowercase prefix
                # followed by capitalized name).
                $line =~ s/\b${oldpkg}_([A-Z])/${newpkg}::$1/xg;

                # Remove package namespace on constructor name (rare)
                $line =~ s/\b${newpkg}::(\w+)::${newpkg}::\1\b/${newpkg}::$1::$1/xg;
            }

            # Translate each old package name to new package name
            my $OLDPKG = uc $oldpkg;
            my $NEWPKG = uc $newpkg;

            # Translate lc and uc package name:
            $line =~ s/(^|[^a-z0-9])${oldpkg}([^a-z0-9])/$1${newpkg}$2/xg;
            $line =~ s/(^|[^A-Z0-9])${OLDPKG}([^A-Z0-9])/$1${NEWPKG}$2/xg;
        }

        $line =~ s/(Copyright \(C\) Bloomberg L.P., 200)[0-9]/${1}7/;
    }

    # Source and dest may actually be the same file.  Close source before
    # opening dest.
    $srcfile->close;

    eval { mkpath(dirname($dstfilename)); };
    my $dstfile = new FileHandle "> $dstfilename";
    die "Cannot open $dstfilename for writing" unless $dstfile;

    print $dstfile @lines;
    
    $dstfile->close;
}

exportToFile($exportfile) if $exportfile;
