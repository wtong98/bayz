r"""
           /\
           | |
      +----|-|---------------------------------------+----------------
    / |    | |             +----+----+----+----+     |        +----+--
   /  |----|/--------------|----|----|----|----|-----|--------|----|--
  /   |   /|               |    |    |    |    |     |        |    |  
 |    |--/-|----b----r-----|----|----|----|----|-----|--r-----|----|--
 |    | |  |               |    |    |    |    |     |        |    |  
 |    |-|-(@)--------------|----|----|----|----|-----|--------|----|--
 |    |  \ |/              |   x|    |   x|    |     |        |   x|  
 |    +----|---------------|---------|---------|-----+--------|-------
  \      o/               x|        x|        x|             x|       
   |                     ---       ---       ---            ---       
  /                        |         |         |             x|       
-|                       -x-       -x-       -x-                      
  \                                                  
   |
  /
 |    +---------------|------------------------------+----------------
 |    |  /^\          |     bayz                     |                
 |    |--o  |:--------|------------------------------|---|------------
 |    |    /          |       band                   |   |            
 |    |---/----------o|------------------R-----------|---|------------
  \   |  /                                           |   |            
   \  |-|-------b------------------------------------|--o|------------
    \ |                                              |                
      +----------------------------------------------+----------------

art by asciiart.eu


To start:
  1. execute the first cell to create a server instance and a new Band
  2. start the WebAudio client at https://wlt.coffee/cream/bayz
  3. type your code in the second cell, and execute to make music!
"""

# <codecell>
from bayz.music import Band
from bayz.server import BayzServer

# start server
server = BayzServer(port=42700)
server.start()

# start band
b = Band(pre_gen=3)
b.connect(server)

# <codecell>
# --- bayz band -o-o-o----------

# Live code here! Uncomment and try the following line
# b.add_player()







# ------------------------------
b.commit()