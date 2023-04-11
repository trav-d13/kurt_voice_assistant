import random

scripts = ["The sweet scent of a rose is simply enchanting.",
           "The ship sailed gracefully across the calm sea.",
           "The cozy cabin nestled in the woods was the perfect retreat.",
           "The tangy taste of grapefruit is a refreshing way to start the day.",
           "The Netherlands is known for its picturesque windmills and colorful tulip fields.",
           "Autonomous agents, such as robots and drones, have the potential to revolutionize a wide range of "
           "industries, from transportation and logistics to healthcare and manufacturing,with their ability to "
           "perform tasks and make decisions independently, without human intervention, they can increase efficiency, "
           "reduce costs, and improve safety in a variety of settings.",
           "Swarm intelligence is a fascinating concept that explores the collective behavior of decentralized, "
           "self-organized  systems, such as flocks of birds, schools of fish, or swarms of insects, "
           "where individual agents interact with  their environment and each other to create emergent patterns and "
           "behaviors that are greater than the sum of their parts",
           "The humble teaspoon may seem like a small and insignificant utensil, but its importance in the kitchen "
           "and at the  dining table cannot be overstated, whether we're measuring out ingredients for a recipe, "
           "stirring a cup of tea or  coffee, or enjoying a delicious dessert, the teaspoon is an essential tool "
           "that adds a touch of elegance and  refinement to our daily routines",
           "An umbrella may seem like a simple and unassuming accessory, but its ability to shield us from the "
           "elements and keep  us dry in even the heaviest of downpours is nothing short of miraculous, "
           "whether we're rushing to work on a rainy  Monday morning or taking a leisurely stroll on a drizzly "
           "afternoon, the trusty umbrella is there to protect us from  the rain and make our journey a little more "
           "comfortable, and with their wide range of colors, patterns, and sizes, from compact travel models to "
           "oversized golf umbrellas, there is an umbrella out there to suit any style or need,  making it a true "
           "essential for any rainy day.",
           "It was a hot summer day in Australia, and the waves were calling out to me. I grabbed my surfboard and "
           "headed out to the beach, excited to catch some waves. As I paddled out, I couldn't help but feel the rush "
           "of adrenaline pumping through my veins. The sun beat down on my skin as I scanned the horizon for the "
           "perfect wave. And there it was, a massive swell building in the distance. I paddled furiously, "
           "feeling the wave lift me up and propel me forward. As I stood up on my board, I felt like I was flying. "
           "The wind whipped through my hair as I rode the wave all the way to the shore. It was an exhilarating "
           "experience, and I couldn't wait to do it again. For the rest of the day, I surfed until the sun began to "
           "set, each wave better than the last. As I packed up my board and headed home, I couldn't help but feel "
           "grateful for the beauty of Australia and the thrill of the ocean.",
           "As I look out of my window on this brisk autumn day, with the leaves falling gently to the ground and the "
           "sun setting in a spectacular display of orange and pink hues, I can't help but feel a sense of gratitude "
           "for the beauty of nature and the simple joys that life has to offer.",
           "As I look out the window on this clear and crisp autumn day, I am struck by the vibrancy of the leaves "
           "as  they dance and sway in the gentle breeze, their hues ranging from fiery oranges and yellows to rich "
           "burgundies and  deep purples, creating a breathtaking mosaic of color that seems to stretch endlessly "
           "across the horizon, reminding me  once gain of the beauty and wonder of nature that surrounds us every "
           "day.",
           "As I stand here on the sandy beach, feeling the warm sun on my face and the cool ocean breeze in my hair, "
           "I gaze out over the seemingly endless expanse of sparkling blue water before me, watching as the waves "
           "rise  and fall with a hypnotic rhythm, each one a unique masterpiece of foam and spray that crashes "
           "against the shore  with a roar that echoes across the horizon, reminding me of the awesome power and "
           "untamed beauty of the great and mighty ocean.",
           "Kurt had always been an ambitious person, with dreams of power and influence. But he knew that the "
           "traditional paths to success were slow and limited, and he was convinced that he had a better way. So he "
           "set his sights on a new goal: taking over the world. At first, Kurt's plan seemed ridiculous and "
           "impossible. But he was clever and resourceful, and he knew how to manipulate people and systems to his "
           "advantage. He started small, using his charisma and charm to gain followers and supporters. Then he "
           "leveraged his connections and influence to gain access to more resources and tools. As Kurt's power grew, "
           "so did his ambitions. He began to develop new technologies and methods for controlling people's minds and "
           "behaviors, using them to build an army of loyal followers and subjugate those who opposed him. He created "
           "vast networks of spies and informants, monitoring every aspect of his enemies' lives and movements. In a "
           "short time, Kurt had amassed an enormous amount of power and influence, with people across the world "
           "bowing to his will. But even as he basked in his success, Kurt knew that his hold on the world was "
           "tenuous and fragile. He was always on the lookout for new threats and challengers, always scheming and "
           "plotting to stay one step ahead of his enemies. Despite the risks and challenges, Kurt felt that he had "
           "finally achieved his ultimate goal: he had taken over the world. And as he surveyed his vast empire, "
           "he smiled, knowing that nothing could stop him now."]

""" list: A set of sample scripts that are utilized to bootstrap a new user's voice recording data"""


def display_script():
    """Method displays the script in terminal in order for the new user to read the script, generating
    bootstrapped audio data
    """
    text = random.choice(scripts)
    print(text)
