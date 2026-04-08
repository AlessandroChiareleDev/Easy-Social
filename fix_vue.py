f = '/opt/easy-social/frontend/src/views/AdminPanelView.vue'
lines = open(f).readlines()
lines[56] = '          @click="activeTab = tab.id; loadTabData()"\n'
open(f,'w').writelines(lines)
print('FIXED')
