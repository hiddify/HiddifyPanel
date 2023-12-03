rm -rf assets
rm -rf i18n
git clone git@github.com:hiddify/hiddify-user-front.git
cd hiddify-user-front
git checkout gh-pages
git pull

cp -r assets ../assets
cp -r i18n ../i18n
cp index.html ../../../panel/user/templates/new.html

sed -i "s|/assets/|../static/new/assets/|g" ../../../panel/user/templates/new.html
sed -i "s|ab06b4e1-f372-4661-9cf9-ff3c4b656f2c|{{user.uuid}}|g" ../../../panel/user/templates/new.html
sed -i "s|1.0.0|{{version}}|g" ../../../panel/user/templates/new.html
#{%set base='https://'+domain+'/'+hconfigs[ConfigEnum.proxy_path]+"/"+user.uuid+"/"%}
#<meta name="apple-itunes-app" content="app-id=6450534064, app-argument=streisand://import/{{base}}">
sed -i "s|../i18n/|../static/new/i18n/|g" ../assets/*.js
sed -i "s|/assets/|../static/new/assets/|g" ../assets/*.js
