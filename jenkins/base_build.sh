#!/bin/bash
export threadfixApiKey=nrct3Mr37NYF1td2UAkuQHNKoPhNRWiMm3hA76iTOIs
export TF_APP_ID=186
export WS=/jslave/workspace/OpenDataStore/extractor-service/extractor-service
echo ""
echo ""
echo ""

echo "Fortify Scan"
echo "SourceAnalyzer Clean by build id - Remove temporary files that might influence a new analysis."
/opt/hp_fortify_sca/bin/sourceanalyzer -64 -b "odsExtractor" -clean
echo ""
echo ""
echo ""
echo "printing work directory"
echo `pwd`
echo "Build by build id -Xmx1024M *.class - Parse source code and prepare for analysis."
/opt/hp_fortify_sca/bin/sourceanalyzer -64 -b "odsExtractor" -Xmx1024M -source "1.7" "." -exclude "$WS/**/*extractor_machine.tgz" "$WS/**/*.fpr"
echo ""
echo ""
echo ""
echo "Analyze the prepared code - Sourceanalyzer scan fortifyResults"
/opt/hp_fortify_sca/bin/sourceanalyzer -64 -b "odsExtractor" -scan -Xmx8096M -f fortifyResults-$BUILD_NUMBER.fpr
echo ""
echo ""
echo ""
echo "Post Fortify Scan to threadfix"
/bin/curl -v --insecure -H 'Accept: application/json' -X POST --form file=@fortifyResults-$BUILD_NUMBER.fpr https://threadfix.gs.mil/rest/applications/$TF_APP_ID/upload?apiKey=$threadfixApiKey

echo "OWASP Dependency Check"
echo "dependency-check.sh"
/opt/dependency-check/bin/dependency-check.sh --project "odsExtractor" --scan "." --format "XML" --enableExperimental
echo ""
echo ""
echo ""

echo "Post OWASP Dependency Check to threadfix"
/bin/curl -v --insecure -H 'Accept: application/json' -X POST --form file=@dependency-check-report.xml https://threadfix.gs.mil/rest/applications/$TF_APP_ID/upload?apiKey=$threadfixApiKey

echo "Post Build and Scan"
tar cvfz app.tar Dockerfile assets/ extractor/ requirements.txt cloudFormation/

tar --list --verbose --file=app.tar

#Clean up on build server
echo "Cleaning up Build Server and workspace"
rm fortifyResults*.fpr
echo "All Clean"

echo "Have a nice day"
