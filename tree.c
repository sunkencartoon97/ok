#include <stdio.h>

int tree[50];

void createtree(int vl) {
    tree[0] = vl;
}

void setleftchild(int i, int val) {
    tree[2 * i + 1] = val;
}

void setrightchild(int i, int val) {
    tree[2 * i + 2] = val;
}

void display() {
    for (int i = 0; i < 50; i++) {
        printf("%d\n", tree[i]);
    }
}

int main() {
    for (int i = 0; i < 50; i++) {
        tree[i] = -1;
    }
    createtree(1); // root
    setleftchild(0, 2);
    setrightchild(0, 3);
    display();
    return 0;
}
