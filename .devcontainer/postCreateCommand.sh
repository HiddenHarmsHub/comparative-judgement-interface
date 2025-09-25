pip3 install -e ".[admin,lint,test]"
npm install
npx puppeteer browsers install chrome
WORKING_DIR=$(pwd)
cp -r $WORKING_DIR/comparison_interface/static/example.images/ $WORKING_DIR/comparison_interface/static/images/
cp $WORKING_DIR/comparison_interface/configuration/example.flask.py $WORKING_DIR/comparison_interface/configuration/flask.py
cp $WORKING_DIR/.env-example $WORKING_DIR/.env
