function Check-CommandExists
{
    param ($command)

    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'

    try
    {
        if (Get-Command $command)
        {
            return
        }
    }
    catch
    {
        Write-Host "ERROR: $command is required"
        exit 1
    }
    finally
    {
        $ErrorActionPreference = $oldPreference
    }
}

function Check-PythonVersion
{
    $pythonVersion = &{python -V} 2>&1

    $matches = [Regex]::Matches($pythonVersion, "[\d\.]+")

    $isGreaterThan = [version]::Parse($matches[0].Value) -ge [version]::Parse("3.6.9")

    if (-not $isGreaterThan)
    {
        Write-Host "ERROR: Darcy AI requires Python 3.6.9 or later"
        exit 1
    }
}

function Check-PythonPackage
{
    param ($package)

    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'

    try
    {
        python -c "import $package" 2>&1
        return
    }
    catch
    {
        Write-Host "ERROR: Python package '$package' is required"
        exit 1
    }
    finally
    {
        $ErrorActionPreference = $oldPreference
    }
}

function Check-OpenCVVersion
{
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'

    try
    {
        python -c 'import cv2; assert cv2.__version__ >= \"3.4.17.63\"' 2>&1
        return
    }
    catch
    {
        Write-Host "ERROR: OpenCV 3.4.17.63 or later is required"
        exit 1
    }
    finally
    {
        $ErrorActionPreference = $oldPreference
    }
}

Check-CommandExists "python"
Check-PythonVersion

Check-CommandExists "docker"

Check-PythonPackage "cv2"
Check-OpenCVVersion

Check-PythonPackage "pycoral"
Check-PythonPackage "darcyai"

Write-Host "Darcy AI development environment is ready"
