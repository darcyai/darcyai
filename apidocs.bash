#!/bin/bash
#
# apiddocs.bash (-h, --help, --generate) - can be used to automatically generate documentation for darcyai
#

# Basic usage function
function usage() {
    echo "Usage: $0 [OPTION]..."
    echo
    echo "  --generate     generate apidocs as html output"
    echo "  -h, --help     display this usage and exit"
}

# Generate api docs
function generate_docs() {
    
    echo "Generating API docs..." >&2
    
    # Generate api docs
    pydoc-markdown

    # Generate site
    pushd pydocs > /dev/null
    mkdocs build
    mv site ../docs
    popd > /dev/null
    rm -R pydocs
    
}

# Run the doc server on localhost:8000
function show_docs() {
    
    # Run the doc server
    pydoc-markdown --server --open
    
}

# Check that pdoc is installed
if ! [ -x "$(command -v pydoc-markdown)" ]; then
    echo "Error: pydoc-markdown is not installed. Please install with 'pip install pydoc-markdown>=4.0.0,<5.0.0 mkdocs'" >&2
    exit 1
fi

# Check for all our options
while :; do
    case $1 in
    -h | --help)
        usage
        exit
        ;;
    --generate)
        generate_docs
        exit
        ;;
    *)
        show_docs
        break
        ;;
    esac
done
